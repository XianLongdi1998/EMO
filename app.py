import psycopg2
from flask import Flask,jsonify
from flask_cors import CORS
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from speech2text import audio_input
from datetime import datetime
import pytz
import os
import re
import google.generativeai as genai
import openai
from flask import request
app = Flask(__name__)
CORS(app)
conn =xxx
secret_id = xxx
secret_key = xxx
region = xxx
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
client = CosS3Client(config)
bucket = xxx

# def uploadaudio(data, path):
#     response = client.put_object(
#         Body=data,
#         Bucket=bucket,
#         Key=f'speak/{path}',
#     )
#     return response
# def uploadaudio(data, path,userid):
#     try:
#         response = client.upload_file(
#             Bucket=bucket,
#             LocalFilePath=f'{data}',
              Key=f'speak/{userid}/{path}',PartSize=1,)
#         return response
#         print(f"Successfully uploaded {path} to Tencent Cloud.")
#         return response
#     except CosServiceError as e:
#         print(f"Failed to upload {path} to Tencent Cloud. Error: {e}")
#         return None

# def text_speech(txt,name):
#     print("generating the text to audio")
#     engine = pyttsx3.init()
#     voices = engine.getProperty('voices')
#     engine.setProperty('voice', voices[-1].id)
#     engine.save_to_file(txt, f"{name}.mp3")
#     engine.runAndWait()
#     return f"{name}.mp3"

# def inputtxt(txt):
#     params = {
#         'model': 'taichu_llm',
#         'messages': [{"role": "user", "content": f"{txt}"}],
#         'stream': False
#     }
#     api = 'https://ai-maas.wair.ac.cn/maas/v1/chat/completions'
#     headers = {'Authorization': 'Bearer v03c043fyzq8ruz8ulj34eb8'}
#     response = requests.post(api, json=params, headers=headers)
#     if response.status_code == 200:
#         result = response.json()
#         content = result['choices'][0]['message']['content']
#         print(content)
#         return content
#     else:
#         body = response.content.decode('utf-8')
#         print(f'request failed, status_code: {response.status_code}, body: {body}')
#         if response.status_code == 403:
#             return "no"
#         return "You need try again"


def inputtxt(txt):
    try:
        api_key = xxx
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        content = f"""{txt}"""
        response = model.generate_content(
            content,
            safety_settings=[
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}
            ],
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                top_p=0.6,
                top_k=5,
                temperature=0.15
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error in summarizing history: {e}")
        return ""


def getul(key):
    response = client.get_presigned_download_url(
        Bucket=bucket,
        Key=key,
        Expired=3600 )
    return response
def clean_text(text):
    cleaned_text = re.sub(r'[^\u4e00-\u9fff，。！？、；：“”‘’（）《》〈〉「」『』【】〔〕…—～]', '', text)
    return cleaned_text

openai.api_key = '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'
openai.default_headers = {"x-foo": "true"}
def chatgpt(txt):
    completion = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"{txt}",
            },
        ],
        max_tokens=150,
        temperature=0.15 
    )
    # print(completion.choices[0].message.content)
    return completion.choices[0].message.content

@app.route("/register", methods=["GET"])
def register():
    try:
        # Retrieve query parameters
        username = request.args.get('username')
        password = request.args.get('password')
        email = request.args.get('email')
        age = request.args.get('age')
        sex = request.args.get('sex')
        phone = request.args.get('phone')
        administrator = request.args.get('Administrator')  # Consider renaming to lowercase for consistency

        # Input validation (basic example)
        if not username or not password or not email:
            return jsonify({"error": "Missing required fields."}), 400  # HTTP 400 Bad Request

        # Get current time in Shanghai timezone
        shanghai_tz = pytz.timezone('Asia/Shanghai')
        current_time = datetime.now(shanghai_tz)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Prepare SQL statement (use placeholders to prevent SQL injection)
        sql = """
        INSERT INTO highlight.usertable (username, password, email, role, age, sex, date, phone, administrator) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        role = 0  # Default role

        # Insert data into the database
        cursor = conn.cursor()
        cursor.execute(sql, (username, password, email, role, age, sex, formatted_time, phone, administrator))
        conn.commit()

        return jsonify({"message": "Registration successful"}), 201  # HTTP 201 Created

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Registration failed."}), 500  # HTTP 500 Internal Server Error

@app.route("/login/<user>", methods=["GET"])
def login(user):
    cursor=conn.cursor()
    sql1=f"""
    select username,password,role from highlight.usertable where username = '{user}';
    """
    cursor.execute(sql1)
    result=cursor.fetchone()
    if result:
        username, password,role = result  # Unpack the tuple directly into username and password
        print(username, password)
    else:
        print("User not found")
    return jsonify({"username": username, "password": password, "role": role})
@app.route("/useresrach/<username>", methods=["GET"])
def useresrach(username):
    cursor = conn.cursor()
    sql1 = f"""
        select * from highlight.usertable where username = '{username}';
        """
    cursor.execute(sql1)
    username = cursor.fetchall()
    print(len(username))
    if len(username)==0:
        username='None'
    else:
        username='have'

    return jsonify({"username": username})

@app.route("/getad", methods=["GET"])
def getad():
    cursor=conn.cursor()
    sql="""
    select username
    from highlight.usertable where
    role = 1;
    """
    cursor.execute(sql)
    allrole=cursor.fetchall()
    res = [
        {
            'username': ro[0]
        } for ro in allrole
    ]
    return jsonify(res)


@app.route("/gethighlight/<userid>/<rqi>/<local>", methods=["GET"])
def getind(userid,rqi,local):
    print(rqi,local)
    # wav=f'xxxxxxx/{local}.mp3'
    # print(local)
    ppath=f'speak/{userid}/speak/{rqi}/{local}'
    wav=getul(ppath)
    text=audio_input(f'{wav}')
    text =clean_text(str(text))
    print("ttttttttttttttttttttttttteeeeeeeeeeeeeeeeeeeeeexxxxxxxxxxxxxxxxxxxxxxtttttttttttttttttt:",text)
    txt1 = f"Please identify any content in the text '{text}' that may lead to feelings of low mood or depression, and precisely mark it with [ ]. If there is no content that may lead to feelings of low mood or depression, please provide the original text directly."
    answers=chatgpt(txt1)
    answers1 = answers.replace('「', '').replace('」', '')
    print("ansersssssssssssssssssssssssssssssssss:",answers1)
    beijing_tz = pytz.timezone('Asia/Shanghai')
    current_date = datetime.now(beijing_tz)
    name=f'{current_date.strftime("%Y%m%d_%H%M%S")}'
    print("nnnnnnnnnnnaaaaaaaaaaaaammmmmmmmmmmmmmmeeeeeeeeeeeee",name)
    ttme=current_date.strftime("%Y-%m-%d %H:%M:%S")
    try:
        curse = conn.cursor()
        sql = f"INSERT INTO highlight.highlight_reply(username, content , content_highlight , date) VALUES ('{userid}', '{text}', '{answers1}', '{ttme}')"
        # data = (userid, text, answers, ttme)
        print(sql)
        curse.execute(sql)
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        # conn.rollback()
    # finally:
    #     if conn:
    #         conn.close()

    return jsonify({
        'suggestions':answers1
    })


@app.route("/videorecord/<userid>/<rqi>/<local>", methods=["GET"])
def videorecord(userid, rqi, local):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT path, path2, label FROM highlight.dmm WHERE username=%s AND date=%s ORDER BY time DESC LIMIT 1",
                (userid, rqi)
            )
            lab = cursor.fetchone()
            beijing_tz = pytz.timezone('Asia/Shanghai')
            current_date = datetime.now(beijing_tz)
            ttme = current_date.strftime("%Y-%m-%d %H:%M:%S")

            if lab:
                path, path2, label = lab

                if path and path2 is None:
                    if int(label) in [1, 2, 3]:
                        cursor.execute(
                            "UPDATE highlight.dmm SET path2=%s WHERE username=%s AND date=%s AND path=%s",
                            (local, userid, rqi, path)
                        )
                elif path and path2 and int(label) in [1, 2]:
                    new_label = int(label) + 1
                    cursor.execute(
                        "INSERT INTO highlight.dmm (username, date, path, label, time) VALUES (%s, %s, %s, %s, %s)",
                        (userid, rqi, local, new_label, ttme)
                    )
            else:
                label = 1
                cursor.execute(
                    "INSERT INTO highlight.dmm (username, date, path, label, time) VALUES (%s, %s, %s, %s, %s)",
                    (userid, rqi, local, label, ttme)
                )
            conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    return jsonify({"status": "success"}), 200


@app.route("/emotionrecord/<userid>/<rqi>/<emo>", methods=["GET"])
def emotionrecord(userid, rqi,emo):
    try:
        emo = emo.strip('[]').split(',')
        emo = [int(e) for e in emo]
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT label FROM highlight.dmm WHERE username=%s AND date=%s ORDER BY time DESC LIMIT 1",
                (userid, rqi)
            )
            lab = cursor.fetchone()
            print(lab)
            cursor.execute(
                "update highlight.dmm set emo=%s,emo1=%s,emo2=%s,emo3=%s where username=%s AND date=%s and label=%s",
                (emo[0],emo[1],emo[2],emo[3],userid, rqi, int(lab[0]))
            )
            conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    return jsonify({"status": "success"}), 200

@app.route("/Allemotion/<userid>", methods=["GET"])
def Allemotion(userid):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""SELECT 
    date,
    ROUND(AVG(avg_emo), 2) as allemo,
    ROUND(AVG(avg_depression), 2) as depression
FROM (
    SELECT 
        date,
        ROUND(AVG((COALESCE(emo, 0) + COALESCE(emo1, 0) + COALESCE(emo2, 0) + COALESCE(emo3, 0)) / 4.0), 2) as avg_emo,
        ROUND(AVG((COALESCE(depression::numeric, 0) + COALESCE(depression1::numeric, 0)) / 2.0), 2) as avg_depression
    FROM 
        highlight.dmm
    WHERE 
        username = '{userid}'
    GROUP BY 
        date, time, label
) sub
GROUP BY 
    date 
ORDER BY 
    date DESC;""")
            allem1 = cursor.fetchall()
            results = [
                {
                    'date': em[0].strftime('%Y-%m-%d'),
                    'allemo': em[1],
                    'depression': 'No risk' if em[2] == 0 else 'Have Risk'
                } for em in allem1
            ]
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    return jsonify(results), 200

@app.route("/Detailemotion/<userid>/<date>", methods=["GET"])
def Detailemotion(userid, date):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    date,
                    positive1 + positive AS positive,
                    negative1 + negative AS negative,
                    duration1 + duration AS duration,
                    CASE 
                        WHEN COALESCE(maxv1, 0) > COALESCE(maxv1, 0) / 2 THEN maxv 
                        ELSE minv 
                    END AS maxv,
                    CASE 
                        WHEN minv1 < minv AND minv1 IS NOT NULL THEN minv
                        WHEN dmm.minv > minv THEN minv
                        ELSE minv1
                    END AS minv,
                    ROUND(AVG((COALESCE(depression::numeric, 0) + COALESCE(depression1::numeric, 0)) / 2.0), 2) AS avg_depression,
                    ROUND(AVG((COALESCE(emo, 0) + COALESCE(emo1, 0) + COALESCE(emo2, 0) + COALESCE(emo3, 0)) / 4.0), 2) AS avg_emo,
                    label,
                    TO_CHAR(time, 'HH24:MI:SS') AS time_str
                FROM
                    highlight.dmm
                WHERE
                    username = %s AND date = %s
                GROUP BY
                    date, time, label, positive1, positive, negative1, negative, 
                    duration1, duration, minv1, minv, maxv1, maxv
                ORDER BY
                    label DESC;
                """,
                (userid, date)  # Pass parameters safely
            )
            allem1 = cursor.fetchall()
            results1 = [
                {
                    'date': em[0].strftime('%Y-%m-%d') if em[0] is not None else '0',  # Format date
                    'poscounts': em[1] if em[1] is not None else 0,
                    'negcounts': em[2] if em[2] is not None else 0,
                    'duration': em[3] if em[3] is not None else 0,
                    'maxVolume': em[4] if em[4] is not None else 0,
                    'minVolume': em[5] if em[5] is not None else 0,
                    'avg_depression': 'No Risk' if em[6] == 0 else 'Have Risk',  # Corrected key name
                    'avg_emo': em[7] if em[7] is not None else 0,  # Corrected key name
                    'label': em[8] if em[8] is not None else 0,
                    'time': em[9] if em[9] is not None else 0
                } for em in allem1
            ]

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    # Return results in JSON format
    return jsonify(results1), 200

@app.route("/userem/<adm>", methods=["GET"])
def userem(adm):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    username,
                    ROUND(AVG((COALESCE(CAST(depression AS NUMERIC), 0) + COALESCE(CAST(depression1 AS NUMERIC), 0)) / 2.0), 2) AS avg_dep,
                    ROUND(AVG((COALESCE(emo, 0) + COALESCE(emo1, 0) + COALESCE(emo2, 0) + COALESCE(emo3, 0)) / 4.0), 2) AS avg_emo
                FROM 
                    highlight.dmm 
                WHERE 
                    username IN (SELECT username FROM highlight.usertable WHERE administrator = %s)
                GROUP BY 
                    username;
                """,
                (adm,)  # Ensure parameters are passed as a tuple
            )
            allem1 = cursor.fetchall()
            results1 = [
                {
                    'username': em[0],
                    'avg_depression':'No Risk' if int(em[1]) == 0 else 'Have Risk',
                    'avg_emo': em[2],
                } for em in allem1
            ]

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    # Return results in JSON format
    return jsonify(results1), 200

@app.route("/userdetail/<user>", methods=["GET"])
def userdetail(user):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """         
SELECT 
    username,
    date,
    ROUND(AVG((COALESCE(CAST(depression AS NUMERIC), 0) + COALESCE(CAST(depression1 AS NUMERIC), 0)) / 2.0), 2) AS avg_dep,
    STRING_AGG(content_highlight, ', ') AS total_content_highlight,
    ROUND(AVG((COALESCE(emo, 0) + COALESCE(emo1, 0) + COALESCE(emo2, 0) + COALESCE(emo3, 0)) / 4.0), 2) AS avg_emo
FROM 
    highlight.dmm 
WHERE 
    username= %s
GROUP BY 
    username, date;
                """,
                (user,)  # Ensure parameters are passed as a tuple
            )
            allem1 = cursor.fetchall()
            results1 = [
                {
                    'username': em[0],
                    'date':em[1].strftime('%Y-%m-%d'),
                    'avg_depression':'No Risk' if int(em[2]) == 0 else 'Have Risk',
                    'text': em[3] if em[3] is not None else '-',
                    'avg_emo': em[4],
                } for em in allem1
            ]

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    # Return results in JSON format
    return jsonify(results1), 200


@app.route("/emotiontext/<userid>/<date>", methods=["GET"])
def emotiontext(userid, date):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    date,
                    label,
                    TO_CHAR(time, 'HH24:MI:SS') as time_str,
                    content,content1,content_highlight ,content_highlight1 
                FROM
                    highlight.dmm
                WHERE
                    username = '{userid}' and date = '{date}'
              
                ORDER BY
                    label ASC;
                """
            )
            allem1 = cursor.fetchall()
            results1 = [
                {'date': em[0].strftime('%Y-%m-%d'), 'label': em[1], 'time': em[2], 'content': em[3], 'content1': em[4], 'content_highlight': em[5], 'content_highlight1': em[6]} for em in allem1
            ]
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    return jsonify(results1), 200


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)