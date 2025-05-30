from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    # Sample DataFrame
    df = pd.DataFrame({
        "Name": ["Alice", "Bob"],
        "Score": [90, 85]
    })
    table_html = df.to_html(classes="table table-striped", index=False)
    return render_template("index.html", table=table_html)
