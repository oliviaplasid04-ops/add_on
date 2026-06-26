import os
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import google.generativeai as genai

from agents.intake import intake
from agents.classify import classify
from agents.sentiment import analyze_sentiment
from agents.priority import assess_priority
from agents.response import generate_response
from agents.delivery import save_to_log, load_log, delete_complaint

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey123")

OFFICER_PASSWORD = os.getenv("OFFICER_PASSWORD", "officer123")
GOOGLE_API_KEY   = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in .env file.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


# ── Helpers ───────────────────────────────────────────────────────────────────
def make_bar_chart(df):
    cat_counts = df["category"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = ax.bar(cat_counts.index, cat_counts.values,
                  color=["#2563EB","#7C3AED","#059669","#DC2626","#D97706","#0891B2"])
    ax.set_xlabel("Category", fontsize=10)
    ax.set_ylabel("Number of Complaints", fontsize=10)
    ax.set_title("Complaints by Category", fontsize=12, fontweight="bold")
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                str(int(bar.get_height())), ha="center", va="bottom", fontsize=9)
    plt.xticks(rotation=25, ha="right", fontsize=8)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def make_priority_chart(df):
    priority_order = ["High", "Medium", "Low"]
    priority_colors = {"High": "#DC2626", "Medium": "#D97706", "Low": "#059669"}
    counts = df["priority"].value_counts().reindex(priority_order, fill_value=0)
    fig, ax = plt.subplots(figsize=(5, 3.5))
    bars = ax.barh(counts.index, counts.values,
                   color=[priority_colors[p] for p in counts.index])
    ax.set_xlabel("Number of Complaints", fontsize=10)
    ax.set_title("Complaints by Priority", fontsize=12, fontweight="bold")
    for bar in bars:
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                str(int(bar.get_width())), va="center", fontsize=9)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("login.html")


@app.route("/login/customer")
def login_customer():
    session["role"] = "customer"
    return redirect(url_for("customer"))


@app.route("/login/officer", methods=["POST"])
def login_officer():
    password = request.form.get("password", "")
    if password == OFFICER_PASSWORD:
        session["role"] = "officer"
        return redirect(url_for("officer"))
    else:
        flash("Incorrect password. Please try again.", "danger")
        return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/customer", methods=["GET", "POST"])
def customer():
    if session.get("role") != "customer":
        return redirect(url_for("index"))

    result = None
    if request.method == "POST":
        name      = request.form.get("name", "").strip()
        complaint = request.form.get("complaint", "").strip()

        if not name or not complaint:
            flash("Please fill in both fields.", "warning")
        else:
            try:
                data      = intake(name, complaint)
                category  = classify(data["complaint"], model)
                sentiment = analyze_sentiment(data["complaint"], model)
                priority  = assess_priority(data["complaint"], sentiment, model)
                reply     = generate_response(data["name"], data["complaint"],
                                              category, sentiment, priority, model)
                save_to_log(data["name"], data["complaint"],
                            category, sentiment, priority, reply)
                result = {"reply": reply, "priority": priority}
            except Exception as e:
                flash(f"Something went wrong: {e}", "danger")

    return render_template("customer.html", result=result)


@app.route("/officer")
def officer():
    if session.get("role") != "officer":
        return redirect(url_for("index"))

    df = load_log()
    complaints = []
    high_alerts = []
    bar_chart = None
    priority_chart = None
    sentiment_summary = []
    stats = {"total": 0, "alerts": 0, "categories": 0}

    if not df.empty:
        stats = {
            "total":      len(df),
            "alerts":     len(df[df["alert"] == "YES"]),
            "categories": df["category"].nunique()
        }

        for i, (idx, row) in enumerate(df.iterrows(), start=1):
            record = {
                "sno":       i,
                "idx":       idx,
                "timestamp": row["timestamp"],
                "name":      row["name"],
                "complaint": row["complaint"],
                "category":  row["category"],
                "sentiment": row["sentiment"],
                "priority":  row["priority"],
                "response":  row["response"],
                "alert":     row["alert"]
            }
            complaints.append(record)
            if row["priority"] == "High":
                high_alerts.append(record)

        bar_chart      = make_bar_chart(df)
        priority_chart = make_priority_chart(df)

        sent_counts = df["sentiment"].value_counts()
        sentiment_summary = [{"sentiment": s, "count": int(c)}
                              for s, c in sent_counts.items()]

    return render_template("officer.html",
                           complaints=complaints,
                           high_alerts=high_alerts,
                           stats=stats,
                           bar_chart=bar_chart,
                           priority_chart=priority_chart,
                           sentiment_summary=sentiment_summary)


@app.route("/delete/<int:idx>", methods=["POST"])
def delete(idx):
    if session.get("role") != "officer":
        return redirect(url_for("index"))
    delete_complaint(idx)
    flash("Complaint deleted successfully.", "success")
    return redirect(url_for("officer"))


@app.route("/download")
def download():
    if session.get("role") != "officer":
        return redirect(url_for("index"))
    from flask import Response
    df = load_log()
    csv = df.to_csv(index=False)
    return Response(csv, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=complaint_log.csv"})


if __name__ == "__main__":
    app.run(debug=True)
