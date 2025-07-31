
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("加重平均キャッシュ生産性 vs 現金増減アプリ")

st.markdown("## 1. 月ごとの製品データ入力")

months = st.multiselect("分析対象の月（例: 2024-01）を選択", options=[
    "2024-01", "2024-02", "2024-03", "2024-04", "2024-05"
], default=["2024-01", "2024-02"])

monthly_data = {}

for month in months:
    st.markdown(f"### 📦 {month}")
    with st.expander(f"{month} の製品データ入力"):
        df = st.data_editor(
            pd.DataFrame(columns=["製品名", "TP（万円）", "LT（日）"]),
            key=month
        )
        cash_start = st.number_input(f"{month}の期首現金残高（万円）", key=f"{month}_start", value=0.0)
        cash_end = st.number_input(f"{month}の期末現金残高（万円）", key=f"{month}_end", value=0.0)
        monthly_data[month] = {"df": df, "start": cash_start, "end": cash_end}

# 計算・集計
results = []

for month, data in monthly_data.items():
    df = data["df"].dropna()
    df["TP/LT"] = df["TP（万円）"] / df["LT（日）"]
    df["TP²/LT"] = df["TP（万円）"]**2 / df["LT（日）"]
    total_tp = df["TP（万円）"].sum()
    weighted_tp_lt = df["TP²/LT"].sum() / total_tp if total_tp > 0 else 0
    cash_diff = data["end"] - data["start"]
    results.append({
        "月": month,
        "加重平均TP/LT": weighted_tp_lt,
        "現金増減額（万円）": cash_diff
    })

# グラフ出力
if results:
    result_df = pd.DataFrame(results)

    st.markdown("## 2. 結果グラフ：加重平均キャッシュ生産性 vs 現金増減額")
    fig, ax = plt.subplots()
    ax.scatter(result_df["加重平均TP/LT"], result_df["現金増減額（万円）"])

    for i, row in result_df.iterrows():
        ax.annotate(row["月"], (row["加重平均TP/LT"], row["現金増減額（万円）"]),
                    textcoords="offset points", xytext=(5, 5), ha='left')

    ax.set_xlabel("加重平均キャッシュ生産性（万円／日）")
    ax.set_ylabel("現金増減額（万円）")
    ax.set_title("月別：加重平均TP/LT vs 現金増減額")
    ax.grid(True)
    st.pyplot(fig)

    # 結果の表とCSVダウンロード
    st.markdown("### 3. 結果表")
    st.dataframe(result_df)

    csv = result_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("CSVをダウンロード", csv, "cash_summary.csv", "text/csv")
