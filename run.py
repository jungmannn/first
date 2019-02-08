from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    print('홈페이지 접속 flask')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)