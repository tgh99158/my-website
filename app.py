from flask import Flask, render_template
from cfbd_rankings import get_rankings
import os

app = Flask(__name__)

@app.route('/')
def index():
    try:
        df = get_rankings()
        return render_template(
            'index.html',
            tables=[df.to_html(classes='data')],
            titles=df.columns.values
        )
    except Exception as e:
        return f"Error fetching data: {e}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)  # Set debug=False for production-like testing







