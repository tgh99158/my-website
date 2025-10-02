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
        # Show the error in the browser instead of crashing the app
        return f"<h2>Error fetching data: {e}</h2>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render provides a PORT
    app.run(host="0.0.0.0", port=port, debug=True)







