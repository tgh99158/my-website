from flask import Flask, render_template
from cfbd_rankings import get_rankings

app = Flask(__name__)

@app.route('/')
def index():
    df = get_rankings()
    return render_template('index.html', tables=[df.to_html(classes='data')], titles=df.columns.values)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # use Render's port, fallback to 5000 locally
    app.run(host="0.0.0.0", port=port)



