# web-grade-app2（WEB制作運用｜名簿＋フォーム統合→採点台帳）

## 目的
- 名簿（RosterMaster）と統合フォーム（FormRaw）をアップロード
- student_no で統合し、未提出者も含めて GradeBook を作る
- email は「最新提出の email」を採用（複数メール対応）
- フォーム提出回数は student_no × 日付 でユニーク（同日二重送信は1回）
- Excel（Roster＋GradeBook）をダウンロード

## 名簿（RosterMaster）必須列
- class
- Timetable
- Time
- student_no
- name

## 起動
```bash
pip install -r requirements.txt
streamlit run app.py
