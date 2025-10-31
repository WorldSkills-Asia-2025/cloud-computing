import boto3
import requests
import time
import uuid
import json
from botocore.exceptions import ClientError
import mysql.connector
from mysql.connector import errorcode

# Insert data before string app
'''
INSERT INTO score (user_id, score) VALUES (101, 1000);
INSERT INTO score (user_id, score) VALUES (102, 1000);
INSERT INTO score (user_id, score) VALUES (103, 1000);
'''

# Change me
PLAYER_ID = ""
PLAYER_URL = ""  # if not exists C.F
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_REGION = ""
SUCCESS_SCORE = 0  # > 0
FAILURE_SCORE = 0  # < 0

# DB configuration
with open('config.json') as f:
    config = json.loads(f.read())

DB_CONFIG = {
    'user': config['user'],
    'password': config['password'],
    'host': config['host'],
    'database': config['database']
}


#########################
# AWS client initialize #
#########################
cf_client = boto3.client(
    "cloudfront",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

######################
# API Check Function #
######################
def is_staticpage_work():
    try:
        for d in get_cf_dns():
            cf_url = d + "/index.html"
            # cf_url = PLAYER_URL
            get_response = requests.get(cf_url)

            if get_response.status_code != 200:
                print("no CloudFront working, " + str(get_response.status_code))
                return False

            # if passed all
            print("API working")
            return True
        
    except requests.exceptions.RequestException as e:
        print("CloudFront call failed:", e)
        return False
    except Exception as e:
        print("CloudFront call failed:", e)
        return False
    
###########
# Utility #
###########
def update_score(user_id, score_delta):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # If exists competitor's score.
        cursor.execute("SELECT score FROM score WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            # Add score
            new_score = result[0] + score_delta
            cursor.execute("UPDATE score SET score = %s WHERE user_id = %s", (new_score, user_id))
            conn.commit()
            print(f"[DB Updated]{user_id}'s score updated {score_delta:+}.")

            return new_score
        else:
            print("No user found")

    except mysql.connector.Error as err:
        print("MySQL error:", err)

def get_cf_dns():
    try:
        out: list[dict] = []
        
        paginator = cf_client.get_paginator("list_distributions")
        for page in paginator.paginate():
            dist_list = page.get("DistributionList", {})
            for d in dist_list.get("Items", []) or []:
                if not d.get("Enabled", False):
                    continue
                out.append(d["DomainName"])  # dxxx.cloudfront.net
        return out
    except Exception as e:
        print("No CloudFront found:", e)
        return False


def main():
    # API test
    if is_staticpage_work():
        new_score = update_score(PLAYER_ID, SUCCESS_SCORE)
    else:
        new_score = update_score(PLAYER_ID, FAILURE_SCORE)

if __name__ == '__main__':
    main()