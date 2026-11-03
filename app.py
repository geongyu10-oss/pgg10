import streamlit as st
import pandas as pd
import soccerdata as sd
import re
import time

st.set_page_config(page_title="유럽 5대 리그 선수 기록 분석", page_icon="⚽", layout="wide")
st.title("⚽ 유럽 5대 리그 선수 시즌 기록 분석")
st.write("선수 이름과 시즌을 입력하면 FBref의 공개 시즌 통계를 찾아 보여줍니다.")

LEAGUE_NAMES = {
    "ENG-Premier League": "프리미어리그",
    "ESP-La Liga": "라리가",
    "GER-Bundesliga": "분데스리가",
    "ITA-Serie A": "세리에 A",
    "FRA-Ligue 1": "리그 1",
}

def flatten_columns(df):
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [
            " ".join(str(x) for x in col if str(x) not in ("", "nan", "None")).strip()
            for col in out.columns.to_list()
        ]
    else:
        out.columns = [str(c) for c in out.columns]
    return out

@st.cache_data(ttl=86400, show_spinner=False)
def load_big5_season(season_text):
    # FBref의 Big 5 통합 선수 시즌 기록을 1회 가져오고 캐시합니다.
    fbref = sd.FBref(
        leagues=["Big 5 European Leagues Combined"],
        seasons=[season_text],
        headless=True,
    )
    frame = fbref.read_player_season_stats(stat_type="standard")
    frame = frame.reset_index()
    frame = flatten_columns(frame)
    return frame

def find_column(columns, candidates):
    lower = {str(c).lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    for c in columns:
        cl = str(c).lower()
        if any(candidate.lower() in cl for candidate in candidates):
            return c
    return None

def display_name(value):
    return str(value).strip() if pd.notna(value) else ""

with st.form("search_form"):
    c1, c2 = st.columns(2)
    with c1:
        player_query = st.text_input("선수 이름", placeholder="예: Son Heung-Min")
    with c2:
        season_query = st.text_input("시즌", value="2023-2024", placeholder="예: 2023-2024")
    submitted = st.form_submit_button("시즌 기록 검색", type="primary", use_container_width=True)

st.caption("선수 이름은 영문 입력을 권장합니다. 시즌은 2023-2024처럼 입력하세요.")

if submitted:
    season_query = season_query.strip()
    if not player_query.strip():
        st.error("선수 이름을 입력해 주세요.")
    elif not re.fullmatch(r"\d{4}[-/]\d{2,4}", season_query):
        st.error("시즌을 2023-2024 형식으로 입력해 주세요.")
    else:
        season_start = int(re.split(r"[-/]", season_query)[0])
        if season_start < 1990 or season_start > 2035:
            st.error("시즌 연도를 확인해 주세요.")
        else:
            try:
                with st.spinner("FBref에서 해당 시즌의 5대 리그 선수 기록을 가져오는 중입니다. 첫 조회는 조금 걸릴 수 있습니다."):
                    df = load_big5_season(season_query)
                player_col = find_column(df.columns, ["player"])
                league_col = find_column(df.columns, ["league"])
                team_col = find_column(df.columns, ["team", "squad"])
                if player_col is None:
                    st.error("가져온 자료에서 선수 이름 항목을 찾지 못했습니다. 다른 시즌으로 다시 시도해 주세요.")
                else:
                    q = player_query.strip().casefold()
                    names = df[player_col].fillna("").astype(str)
                    matches = df[names.str.casefold().str.contains(re.escape(q), na=False)].copy()
                    if matches.empty:
                        st.warning("해당 시즌에서 선수를 찾지 못했습니다. 영문 이름 일부만 입력해 다시 검색해 보세요.")
                    else:
                        matches["_display"] = matches[player_col].astype(str)
                        choices = matches.drop_duplicates(subset=["_display"])
                        chosen_name = st.selectbox("검색된 선수 선택", choices["_display"].tolist())
                        selected = matches[matches["_display"] == chosen_name].copy()

                        if league_col:
                            league_text = selected[league_col].astype(str)
                            selected = selected[
                                league_text.str.contains(
                                    "Premier League|La Liga|Bundesliga|Serie A|Ligue 1",
                                    case=False, regex=True, na=False
                                )
                            ]

                        st.subheader(f"{chosen_name} · {season_query} 시즌")
                        if selected.empty:
                            st.info("선수는 검색됐지만 5대 리그 소속 기록을 구분하지 못했습니다.")
                        else:
                            for row_no, (_, row) in enumerate(selected.iterrows()):
                                league_value = str(row[league_col]) if league_col else "유럽 5대 리그"
                                team_value = str(row[team_col]) if team_col else "-"
                                st.markdown(f"### {league_value} · {team_value}")

                                # FBref 기본 시즌 통계 열 이름에 맞춰 항목을 찾아 표시합니다.
                                field_map = [
                                    ("출전 경기", ["MP"]),
                                    ("선발 출전", ["Starts"]),
                                    ("출전 시간(분)", ["Min"]),
                                    ("90분 환산 출전", ["90s"]),
                                    ("골", ["Gls"]),
                                    ("도움", ["Ast"]),
                                    ("골+도움", ["G+A"]),
                                    ("페널티킥 골", ["PK"]),
                                    ("경고", ["CrdY"]),
                                    ("퇴장", ["CrdR"]),
                                ]
                                values = []
                                for label, candidates in field_map:
                                    col = find_column(selected.columns, candidates)
                                    values.append((label, row[col] if col else "-"))

                                metric_rows = [values[i:i+5] for i in range(0, len(values), 5)]
                                for group in metric_rows:
                                    cols = st.columns(len(group))
                                    for col_ui, (label, value) in zip(cols, group):
                                        if pd.isna(value):
                                            value = "-"
                                        col_ui.metric(label, str(value))

                                # 찾을 수 있는 통계만 표에 담아 출처 열 이름도 보존합니다.
                                preferred = [
                                    "MP", "Starts", "Min", "90s", "Gls", "Ast", "G+A",
                                    "PK", "PKatt", "CrdY", "CrdR"
                                ]
                                actual_cols = []
                                for item in preferred:
                                    found = find_column(selected.columns, [item])
                                    if found and found not in actual_cols:
                                        actual_cols.append(found)
                                if actual_cols:
                                    table = pd.DataFrame({
                                        "기록 항목": actual_cols,
                                        "시즌 기록": [row[c] if pd.notna(row[c]) else "-" for c in actual_cols]
                                    })
                                    st.dataframe(table, hide_index=True, use_container_width=True)
                                    st.download_button(
                                        "이 선수 기록 CSV 다운로드",
                                        table.to_csv(index=False).encode("utf-8-sig"),
                                        file_name=f"player_{season_query}_{row_no+1}.csv",
                                        mime="text/csv",
                                        key=f"download_{row_no}"
                                    )
            except Exception as exc:
                st.error("자료를 불러오지 못했습니다. FBref 접속 제한 또는 해당 시즌 자료 문제일 수 있습니다.")
                st.caption(f"오류 내용: {type(exc).__name__}: {exc}")
                st.info("잠시 후 다시 시도하거나, FBref 사이트에서 해당 시즌의 기록이 제공되는지 확인해 주세요.")

st.divider()
with st.expander("자료 출처 및 이용 안내"):
    st.markdown("""
    - 자료 출처: [FBref 유럽 5대 리그 통계](https://fbref.com/en/comps/Big5/)
    - 수집 도구: [soccerdata 오픈소스 라이브러리](https://soccerdata.readthedocs.io/)
    - 검색 범위: 프리미어리그, 라리가, 분데스리가, 세리에 A, 리그 1
    - 기본 기록: 출전 경기, 선발, 출전 시간, 골, 도움, 페널티킥, 경고, 퇴장 등
    - 데이터가 없는 선수·시즌은 검색되지 않을 수 있습니다.
    - 첫 조회는 웹에서 자료를 가져오므로 시간이 걸리며, 같은 시즌은 캐시에 저장해 재조회 시간을 줄입니다.
    - FBref의 접속 제한과 이용 정책을 준수하며 짧은 시간에 반복 검색하지 마세요.
    """)
