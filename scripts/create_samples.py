"""Generate four compatible import examples from the application's sample catalog."""
import csv
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
def write(name,headers,rows):
    with (Path('samples')/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(headers);w.writerows(rows)
def main():
    from app.services.import_samples import sample_rows
    from app.services.csv_import import HEADERS
    Path('samples').mkdir(exist_ok=True)
    students=['id','name','class_id','advisor_id','admission_score','admission_scale','admission_method']
    results=['student_id','semester_id','gpa','cumulative_gpa','registered','passed','failed','accumulated','conduct','status']
    for kind,rows in sample_rows().items():
        write(kind+'_valid.csv',HEADERS[kind],[[str(row[key]).lower() if isinstance(row[key],bool) else row[key] for key in HEADERS[kind]] for row in rows])
    write('students_errors.csv',students,[['009002','Sai thang điểm','L1',2,35,30,'THPT'],['009003','Lớp chưa có','XX',2,24,30,'THPT'],['009002','Trùng mã trong tệp','L1',2,24,30,'THPT']])
    write('results_errors.csv',results,[['2351999001',6,5,2.4,20,12,8,100,75,'completed'],['2351999001',5,2.3,2.4,20,20,8,100,75,'completed'],['NO_STUDENT',6,2,2.4,20,12,8,100,75,'completed']])
    print('Created 6 synthetic CSV examples.')
if __name__=='__main__':main()
