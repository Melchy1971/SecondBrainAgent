import json, shutil
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

class Store:
    def __init__(self, root='.'):
        self.root = Path(root)
        self.base = self.root / 'data' / 'installer_update'
        self.base.mkdir(parents=True, exist_ok=True)
    def load(self, name, default):
        path = self.base / f'{name}.json'
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
    def save(self, name, value):
        (self.base / f'{name}.json').write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    def append(self, name, item):
        items = self.load(name, [])
        items.append(item)
        self.save(name, items)
        return item

class InstallerUpdateRuntime:
    def __init__(self, root='.'):
        self.root = Path(root)
        self.store = Store(root)
        self.backup_dir = self.root / 'update_backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    def manifest_create(self, version='15.2'):
        m = {'name':'SecondBrain OS','version':version,'channel':'local','required_files':['launcher.py','secondbrain','requirements.txt'],'rollback_supported':True,'created_at':datetime.now(timezone.utc).isoformat()}
        self.store.save('release_manifest', m)
        return m
    def manifest(self):
        existing = self.store.load('release_manifest', None)
        return existing or self.manifest_create('15.2')
    def validate(self):
        checks=[]
        for name in ['launcher.py','secondbrain','requirements.txt']:
            p=self.root/name
            checks.append({'name':name,'exists':p.exists(),'path':str(p)})
        return {'ok': all(c['exists'] for c in checks), 'checks': checks}
    def status(self):
        return {'version':'15.2','manifest':self.manifest(),'config':self.validate(),'backups':len(self.backups()),'update_runs':len(self.store.load('update_runs',[]))}
    def portable_plan(self, target_dir):
        return {'target_dir':str(Path(target_dir)),'portable':True,'steps':['create_directory','copy_project_files','create_config','run_validation']}
    def portable_marker(self, target_dir):
        return self.store.append('installations', {'id':str(uuid4()),'target_dir':str(Path(target_dir)),'status':'planned','created_at':datetime.now(timezone.utc).isoformat()})
    def update_check(self, current_version='unknown'):
        m=self.manifest()
        return {'current_version':current_version,'available_version':m['version'],'update_available':current_version != m['version'],'channel':m['channel']}
    def update_plan(self, current_version='unknown'):
        v=self.validate(); c=self.update_check(current_version)
        plan={'id':str(uuid4()),'current_version':current_version,'target_version':c['available_version'],'can_update':v['ok'],'steps':['validate_config','backup','apply_files','smoke_test','mark_version'],'validation':v,'created_at':datetime.now(timezone.utc).isoformat()}
        self.store.save('latest_update_plan', plan)
        return plan
    def backup_create(self, from_version='unknown', to_version='15.2'):
        bid=str(uuid4()); target=self.backup_dir/bid; target.mkdir(parents=True, exist_ok=True)
        data=self.root/'data'
        if data.exists(): shutil.copytree(data,target/'data',dirs_exist_ok=True)
        item={'id':bid,'from_version':from_version,'to_version':to_version,'path':str(target),'status':'created','created_at':datetime.now(timezone.utc).isoformat()}
        return self.store.append('update_backups', item)
    def backups(self):
        return self.store.load('update_backups', [])
    def update_run(self, current_version='unknown'):
        plan=self.update_plan(current_version)
        if not plan['can_update']:
            return {'ok':False,'error':'validation_failed','plan':plan}
        backup=self.backup_create(current_version, plan['target_version'])
        run={'ok':True,'plan':plan,'backup':backup,'status':'simulated_success','applied_at':datetime.now(timezone.utc).isoformat()}
        self.store.append('update_runs', run)
        return run
    def rollback_plan(self, backup_id):
        backup=next((b for b in self.backups() if b['id']==backup_id), None)
        if not backup: return {'ok':False,'error':'backup_not_found'}
        return {'ok':True,'backup':backup,'steps':['stop_runtime','restore_backup_data','validate','start_runtime']}
