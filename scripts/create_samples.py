"""Generate import examples with only Python's standard library."""
import csv
from pathlib import Path
def write(name,headers,rows):
    with (Path('samples')/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(headers);w.writerows(rows)
def main():
    Path('samples').mkdir(exist_ok=True)
    students=['id','name','class_id','advisor_id','admission_score','admission_scale','admission_method']
    results=['student_id','semester_id','gpa','cumulative_gpa','registered','passed','failed','accumulated','conduct','status']
    write('students_valid.csv',students,[['009001','Sinh viên nhập mẫu — Dữ liệu giả lập','L1',2,24,30,'THPT giả lập']])
    write('results_valid.csv',results,[['009001',n,g,2.4,20,p,20-p,a,75,'completed'] for n,g,p,a in [(1,3,20,20),(2,3,20,40),(3,3,20,60),(4,2.8,18,78),(5,2.3,16,94),(6,1.9,12,106)]])
    write('debts_valid.csv',['student_id','semester_id','course_id'],[['009001',6,'HP01']])
    write('warnings_valid.csv',['student_id','semester_id','warned'],[['009001',n,str(n in (4,5)).lower()] for n in range(1,7)])
    write('students_errors.csv',students,[['009002','Sai thang điểm','L1',2,35,30,'THPT'],['009003','Lớp chưa có','XX',2,24,30,'THPT'],['009002','Trùng mã trong tệp','L1',2,24,30,'THPT']])
    write('results_errors.csv',results,[['009001',6,5,2.4,20,12,8,100,75,'completed'],['009001',5,2.3,2.4,20,20,8,100,75,'completed'],['NO_STUDENT',6,2,2.4,20,12,8,100,75,'completed']])
    print('Created 6 synthetic CSV examples.')
if __name__=='__main__':main()
