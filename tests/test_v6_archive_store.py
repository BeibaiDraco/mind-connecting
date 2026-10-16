import json
from pathlib import Path
import zipfile
import pytest
from mb.v6_archive_store import pack,restore as raw_restore,sha256


def restore(directory,output,**kwargs):
    return raw_restore(directory,output,expected_manifest_sha256=sha256(directory/"manifest.json"),**kwargs)


def sources(tmp_path):
    rows=[]
    for i in range(3):
        p=tmp_path/f"original{i}.pt"
        with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_STORED) as z:
            z.writestr("archive/data.pkl",b"not executable pickle: "+bytes([i]))
            z.writestr("archive/data/0",bytes(range(256))*16+b"x"*(i+1)*1024)
            z.writestr("archive/data/1",bytes(range(256))*16)
        rows.append({"name":p.name,"path":p,"bytes":p.stat().st_size,"sha256":sha256(p)})
    return rows


def test_full_original_file_roundtrip_with_stored_zip_boundaries(tmp_path):
    rows=sources(tmp_path); before=[r["path"].read_bytes() for r in rows]
    m=pack(rows,tmp_path/"packed")
    out=restore(tmp_path/"packed",tmp_path/"restored",cache_bytes=1024)
    assert out["status"]=="restored_exact_bytes"
    for row,original in zip(rows,before):
        assert (tmp_path/"restored"/row["name"]).read_bytes()==original
        assert row["path"].read_bytes()==original
    assert sum(r["bytes"] for r in m["container"].values())<sum(r["bytes"] for r in rows)
    with pytest.raises(FileExistsError): pack(rows,tmp_path/"packed")
    with pytest.raises(FileExistsError): restore(tmp_path/"packed",tmp_path/"restored")


@pytest.mark.parametrize("file",["blocks.bin","index.bin","refs.bin"])
def test_container_corruption_refused_before_restore(tmp_path,file):
    pack(sources(tmp_path),tmp_path/"packed")
    p=tmp_path/"packed"/file; raw=bytearray(p.read_bytes()); raw[-1]^=1; p.write_bytes(raw)
    with pytest.raises(ValueError,match="checksum"): restore(tmp_path/"packed",tmp_path/"restored")
    assert not (tmp_path/"restored").exists()


def test_failed_pack_retained_and_not_reused(tmp_path):
    rows=sources(tmp_path); rows[-1]["sha256"]="0"*64
    with pytest.raises(ValueError,match="integrity"): pack(rows,tmp_path/"failed")
    assert (tmp_path/"failed"/"blocks.bin").exists()
    assert not (tmp_path/"failed"/"manifest.json").exists()
    with pytest.raises(FileExistsError): pack(sources(tmp_path),tmp_path/"failed")


def test_bounded_metadata_and_missing_file_fail_closed(tmp_path):
    rows=sources(tmp_path)
    with pytest.raises(ValueError,match="bound"): pack(rows,tmp_path/"bounded",max_blocks=1)
    rows[0]["path"]=tmp_path/"missing"
    with pytest.raises(ValueError): pack(rows,tmp_path/"missing-output")
    assert not (tmp_path/"missing-output").exists()


@pytest.mark.parametrize("name",["../bad","/bad",".","restore_receipt.json"])
def test_output_path_or_receipt_collision_refused(tmp_path,name):
    rows=sources(tmp_path); rows[0]["name"]=name
    with pytest.raises(ValueError): pack(rows,tmp_path/"packed")


def test_empty_file_and_no_cache(tmp_path):
    p=tmp_path/"empty";p.write_bytes(b"")
    pack([{"name":p.name,"path":p,"bytes":0,"sha256":sha256(p)}],tmp_path/"packed")
    restore(tmp_path/"packed",tmp_path/"restored",cache_bytes=0)
    assert (tmp_path/"restored"/"empty").read_bytes()==b""


def test_declared_original_hash_still_checked_after_container_validation(tmp_path):
    pack(sources(tmp_path),tmp_path/"packed")
    p=tmp_path/"packed"/"manifest.json"; m=json.loads(p.read_text())
    m["files"][0]["sha256"]="0"*64;p.write_text(json.dumps(m))
    with pytest.raises(ValueError,match="Original file"): restore(tmp_path/"packed",tmp_path/"bad")
    assert not (tmp_path/"bad"/"restore_receipt.json").exists()


def test_external_manifest_binding_detects_valid_file_rename(tmp_path):
    pack(sources(tmp_path),tmp_path/"packed")
    p=tmp_path/"packed"/"manifest.json"; digest=sha256(p); m=json.loads(p.read_text())
    m["files"][0]["name"]="renamed.pt";p.write_text(json.dumps(m))
    with pytest.raises(ValueError,match="Externally bound"):
        raw_restore(tmp_path/"packed",tmp_path/"bad",expected_manifest_sha256=digest)
    assert not (tmp_path/"bad").exists()
