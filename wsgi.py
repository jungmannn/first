# 엔트리파일 (진입점) -> 서버구동 시 run 파일
# 아파치 서버가 이 파일을 구동하여 flask 가동시킴
# 여기서는 Flask 객체를 가져와서 참조

import sys
import os

# 경로 설정
CUR_DIR = os.getcwd()
# 에러의 출력방향과 동일하게 일반 출력 방향 설정
sys.stdout = sys.stderr
sys.path.insert(0, CUR_DIR)

# 서버 가져오기
from run import app as application

