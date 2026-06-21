from secondbrain.installer_update import InstallerUpdateRuntime

def prepared(tmp_path):
    (tmp_path/'launcher.py').write_text('')
    (tmp_path/'secondbrain').mkdir()
    (tmp_path/'requirements.txt').write_text('')
    return tmp_path

def test_status(tmp_path):
    rt=InstallerUpdateRuntime(prepared(tmp_path))
    assert rt.status()['version']=='15.2'

def test_validate(tmp_path):
    rt=InstallerUpdateRuntime(prepared(tmp_path))
    assert rt.validate()['ok'] is True

def test_manifest(tmp_path):
    rt=InstallerUpdateRuntime(tmp_path)
    assert rt.manifest_create('15.2')['rollback_supported'] is True

def test_update_and_rollback(tmp_path):
    rt=InstallerUpdateRuntime(prepared(tmp_path))
    run=rt.update_run('15.1')
    assert run['ok'] is True
    assert rt.rollback_plan(run['backup']['id'])['ok'] is True

def test_portable_plan(tmp_path):
    rt=InstallerUpdateRuntime(tmp_path)
    assert rt.portable_plan('H:/SecondBrainAgent')['portable'] is True
