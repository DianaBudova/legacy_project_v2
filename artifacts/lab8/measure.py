import ast, json, os, subprocess, sys
from pathlib import Path
phase=sys.argv[1]
out=Path('artifacts/lab8')/phase
out.mkdir(exist_ok=True)
env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYLINTHOME='/tmp/lab8/pylint', COVERAGE_FILE='/tmp/lab8/.coverage')
commands={
 'pytest':[sys.executable,'-m','pytest','tests/','-v','-p','no:cacheprovider','--cov=src','--cov-config=artifacts/lab8/coverage.ini','--cov-report=term-missing','--cov-report=json:'+str(out/'coverage.json')],
 'pylint':[sys.executable,'-m','pylint','src/process.py','--score=y','--persistent=n'],
 'radon':[sys.executable,'-m','radon','cc','src/process.py','-s'],
 'radon_json':[sys.executable,'-m','radon','cc','src/process.py','-j'],
 'pylint_json':[sys.executable,'-m','pylint','src/process.py','--output-format=json','--persistent=n']}
if phase == 'before':
 commands['pytest'].extend(['--ignore=tests/test_process.py'])
for name,cmd in commands.items():
 r=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (out/(name+'.txt')).write_text('$ '+' '.join(cmd[2:])+'\n'+r.stdout if name not in ['radon_json','pylint_json'] else r.stdout)
 print(name,'exit',r.returncode)
source=Path('src/process.py').read_text()
funcs=[{'name':n.name,'line':n.lineno,'loc':n.end_lineno-n.lineno+1} for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)]
(out/'structure.json').write_text(json.dumps({'loc':len(source.splitlines()),'functions':funcs},indent=2))
