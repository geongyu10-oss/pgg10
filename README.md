# 유럽 5대 리그 선수 시즌 기록 분석

선수 이름과 시즌을 입력하면 FBref의 유럽 5대 리그 통합 시즌 통계에서 선수를 찾아 기록을 표시하는 Streamlit 앱입니다.

## 검색 범위
- 잉글랜드 프리미어리그
- 스페인 라리가
- 독일 분데스리가
- 이탈리아 세리에 A
- 프랑스 리그 1

## 실행 방법
1. `pip install -r requirements.txt`
2. `streamlit run app.py`
3. 선수 이름(영문 권장)과 시즌(예: `2023-2024`)을 입력합니다.

## GitHub / Streamlit 배포
저장소 루트에 `app.py`, `requirements.txt`, `packages.txt`, `README.md`를 올립니다.
Streamlit Community Cloud에서 저장소를 선택하고 Main file path를 `app.py`로 설정해 배포합니다.

## 자료 출처
- FBref: https://fbref.com/en/comps/Big5/
- soccerdata: https://soccerdata.readthedocs.io/

첫 조회는 FBref 자료를 내려받기 때문에 시간이 걸릴 수 있습니다. 조회 결과는 하루 동안 캐시됩니다. FBref의 이용약관 및 자동 접속 제한을 준수하고 반복 조회를 자제하세요.
