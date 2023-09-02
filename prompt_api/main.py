import os
import csv
import re
import urllib.request
import pandas as pd
import time
from datetime import datetime

from ast import literal_eval

from dotenv import load_dotenv

from gpt_prompt import gpt_input_values #gpt로 결과 출력
from dalle import use_dalle #달리로 url출력

from fastapi import FastAPI, Form
from typing import Optional, Union, Annotated
from pydantic import BaseModel

from firebase_admin import credentials, initialize_app, storage

load_dotenv()
storage_bucket_name = os.getenv("storage_bucket_name")

# 파이어베이스 연결
cred = credentials.Certificate('firebase_key.json')
initialize_app(cred, {
    'storageBucket': storage_bucket_name
})
bucket = storage.bucket()

###### csv(DB역할) 미리 생성 ######

# 유저 정보 csv
User_Info_columns = ["user_id","user_sex","user_age","user_job","user_prefer","keyword1","keyword2","keyword3","keyword4","keyword5"]
if os.path.isfile('User_Info.csv') == False:
    with open('User_Info.csv', mode='w', newline='') as f:
            csv_writer = csv.writer(f, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(User_Info_columns)
            f.close()

# 유저가 저장한 이미지 정보
User_Save_Img_columns = ["user_id","save_img_idx_list"]
if os.path.isfile('User_Save_Img.csv') == False:
    with open('User_Save_Img.csv', mode='w', newline='') as f:
            csv_writer = csv.writer(f, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(User_Save_Img_columns)
            f.close()

# 타겟팅 정보
Targeting_Info_columns = ["user_id","target_sex","target_age","target_job","target_prefer","more_info","product","target_keyword1","target_keyword2","chatgpt_summary","chatgpt_reason","img_idx"]
if os.path.isfile('Targeting_Info.csv') == False:
    with open('Targeting_Info.csv', mode='w', newline='') as f:
            csv_writer = csv.writer(f, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(Targeting_Info_columns)
            f.close()


# 타겟팅에서 나온 이미지 정보
Targeting_Image_Info_columns = ["user_id","img_idx","img_title","img_url","img_create_date"]
if os.path.isfile('Targeting_Image_Info.csv') == False:
    with open('Targeting_Image_Info.csv', mode='w', newline='') as f:
            csv_writer = csv.writer(f, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(Targeting_Image_Info_columns)
            f.close()


# 이미지 상세 정보 [좋아요 갯수, 좋아요 누른 사람 리스트]
Image_More_Info_columns = ["img_idx","img_liked","img_liked_user_list"]
if os.path.isfile('Image_More_Info.csv') == False:
    with open('Image_More_Info.csv', mode='w', newline='') as f:
            csv_writer = csv.writer(f, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(Image_More_Info_columns)
            f.close()


# class user_info_p(BaseModel):
#     user_id : str
#     user_sex : str
#     user_age : str
#     user_job : str
#     user_prefer : str
#     keyword1 : Optional[str] = None
#     keyword2 : Optional[str] = None
#     keyword3 : Optional[str] = None
#     keyword4 : Optional[str] = None
#     keyword5 : Optional[str] = None



app = FastAPI()

@app.get('/')
async def root():
    return {'hello': 'world'}

# ---------------------완료-----------------------
# 유저 - 기본정보 등록
@app.post('/user_info')
async def User_Info( user_id: int = Form(...),
                     user_sex: str = Form(...),
                     user_age: str = Form(...),
                     user_job: str = Form(...),
                     user_prefer: str = Form(...),
                     keyword1: Annotated[str,Form()] = None,
                     keyword2: Annotated[str,Form()] = None,
                     keyword3: Annotated[str,Form()] = None,
                     keyword4: Annotated[str,Form()] = None,
                     keyword5: Annotated[str,Form()] = None
    ):


    # User_Info csv파일에 추가
    UT_list = [user_id,user_sex,user_age,user_job,user_prefer, keyword1, keyword2, keyword3, keyword4, keyword5]
    with open('User_info.csv', mode='a', newline='') as f: # 계속 추가할거기 때문에 mode='a'
                    csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    csv_writer.writerow(UT_list)
                    f.close()

    return {"result" : "success"}    

# ---------------------완료-----------------------
# 홈 - 모든 이미지 받기
@app.post('/home_get_all_images')
async def Home_Get_All_Images(
     user_id : int = Form(...),
     ):
      
    df = pd.read_csv("Targeting_Image_Info.csv")

    home_all_images = []
    
    for i in range(len(df)):
        home_all_images.append(df.loc[i,["img_idx","img_url",'img_create_date']].to_dict())

    home_all_images = sorted(home_all_images, key=lambda x :x['img_create_date'], reverse=True)
    print(home_all_images)
    return {"result":home_all_images}

# ---------------------완료-----------------------
# 홈 - 이미지 상세정보 : title과 좋아요 수
@app.post('/home_image_info')
async def Home_Image_Info(
     user_id : int = Form(...),
     img_idx : int = Form(...)
     ):
      
    df = pd.read_csv("Targeting_Image_info.csv")
    liked_df = pd.read_csv("Image_More_Info.csv")

    img_title = df[df['img_idx'] == img_idx]['img_title'].values[0]
    print(img_title)
    img_liked = liked_df[liked_df['img_idx'] == img_idx]['img_liked'].values[0]
    print(img_liked)
    
    result = {"img_title" : img_title,
              "img_liked" : int(img_liked)} 

    return result


# 홈 - 이미지 상세정보 : 상세 정보에서 비율 보기
@app.post('/home_image_detail_info')
async def Home_Image_Detail_Info(
     user_id : int = Form(...),
     img_idx : int = Form(...)
     ):

    img_more_df = pd.read_csv("Image_More_Info.csv")

    user_df = pd.read_csv("User_Info.csv")

    # 이미지를 좋아한 사람들의 id 리스트
    user_liked_list = literal_eval(img_more_df[img_more_df['img_idx'] == img_idx]['img_liked_user_list'].values[0])

    # 좋아한 사람 수
    print("좋아한 사람 수 : ", len(user_liked_list))

    ########################## 남자, 여자 비율과 나이 비율 #################################
    sex_dict = {}
    
    age_dict = {}
    
    prefer_dict = {}

    
    for i in user_liked_list:
        same_id_df = user_df[user_df['user_id'] == i]
        user_sex_age_prefer = list(same_id_df[['user_sex','user_age','user_prefer']].values[0])
        # print(user_sex_age_prefer)

        ### 성별 비율 구하기
        if user_sex_age_prefer[0] not in sex_dict.keys():
            sex_dict[user_sex_age_prefer[0]] = 1
        else :
            sex_dict[user_sex_age_prefer[0]] += 1


        ### 나이 비율 구하기
        if user_sex_age_prefer[1] not in age_dict.keys():
            age_dict[user_sex_age_prefer[1]] = 1
        else :
            age_dict[user_sex_age_prefer[1]] += 1

        ### 선호 비율 구하기
        if user_sex_age_prefer[2] not in prefer_dict.keys():
            prefer_dict[user_sex_age_prefer[2]] = 1
        else :
            prefer_dict[user_sex_age_prefer[2]] += 1
    
    print(sex_dict)
    print(age_dict)
    print(prefer_dict)

    ### 나이 비율 추출
    sex_result = []
    for key,value in sex_dict.items():
        sex_result.append({key : value,
                            "sex_ratio" : str(round(value/len(user_liked_list),2))+"%"})


    ### age top 2 추출
    sort_age = sorted(age_dict.items(), key=lambda x: x[1], reverse=True)[:2]
    age_result = []
    for x in sort_age:
        age_result.append({"age" : x[0],
                            "age_ratio" : str(round(x[1]/len(user_liked_list),2))+"%"})

    ### prefer top3 추출
    sort_prefer = sorted(prefer_dict.items(), key=lambda x: x[1], reverse=True)[:3]
    prefer_result = []
    for x in sort_prefer:
        prefer_result.append({"prefer" : x[0],
                            "prefer_ratio" : str(round(x[1]/len(user_liked_list),2))+"%"})


    result = {
                "sex_ratio" : sex_result,
                "age" : age_result,
                "prefer" : prefer_result
    }

    return result

# # 홈 - 이미지 상세정보 가져오기 : 상세정보 보기
# @app.post('/home_image_info')
# async def Home_Image_Info(
#      user_id : int = Form(...),


# ---------------------완료-----------------------
# 홈 - 이미지 좋아요 버튼
@app.post('/home_image_liked')
async def Home_Image_Liked(
     user_id : int = Form(...),
     img_idx : int = Form(...)
     ):
    

    df = pd.read_csv("Image_More_Info.csv")
    
    if img_idx in df['img_idx'].values:     
        
        df.loc[df[df['img_idx'] == img_idx].index,'img_liked'] = df['img_liked'] + 1
        print("aaaaaaaa")
        img_liked_send_user_list = literal_eval(df.loc[df[df['img_idx'] == img_idx].index,'img_liked_user_list'].values[0])
        img_liked_send_user_list.append(user_id)
        
        df.loc[df[df['img_idx'] == img_idx].index,'img_liked_user_list'] = str(img_liked_send_user_list)
        df.to_csv("Image_More_Info.csv", index=False)

    else:

        # 이미지 상세 정보 [좋아요 갯수, 좋아요 누른 사람 리스트]
        Image_More_Info_columns = [img_idx,1,[user_id]]
        with open('Image_More_Info.csv', mode='a', newline='') as f:
                csv_writer = csv.writer(f, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow(Image_More_Info_columns)
                f.close()

    liked_count_df = pd.read_csv("Image_More_Info.csv")
    liked_count = liked_count_df[liked_count_df['img_idx'] == img_idx]['img_liked'].values[0]
    print(liked_count)
    print(f"{user_id} liked {img_idx}, count is {liked_count}")

    return {"liked_count" : str(liked_count)}

# ---------------------완료-----------------------
# 홈 - 이미지 포크 버튼
@app.post('/home_fork_image')
async def Home_Fork_Image(
     user_id : int = Form(...),
     img_idx : int = Form(...)
     ):

    df = pd.read_csv("User_Save_Img.csv")
    if user_id in df['user_id'].values:

        save_imgs_idx_list = literal_eval(df.loc[df[df['user_id']==user_id].index[0], 'save_img_idx_list'])

        save_imgs_idx_list.append(img_idx)

        df.loc[df[df['user_id']==user_id].index[0], 'save_img_idx_list'] = str(save_imgs_idx_list)
        df.to_csv("User_Save_Img.csv", index=False)

    else:
        # 유저 이미지 저장 정보
        User_Save_Img_columns = [user_id,[img_idx]]
        with open('User_Save_Img.csv', mode='a', newline='') as f:
                csv_writer = csv.writer(f, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow(User_Save_Img_columns)
                f.close()


    return {"result":"ok"}

# ---------------------완료-----------------------
# 타겟팅 - Chat-gpt 프롬프트 생성
@app.post('/targeting_create_prompt')
async def Targeting_Create_Prompt(
     user_id : int = Form(...),
     target_sex : str = Form(...),
     target_age : str = Form(...),
     target_job : str = Form(...),
     target_prefer : str = Form(...),
     product : str = Form(...),
     more_info : Annotated[str,Form()] = None,
    ):
    
    print("start to create prompt")
    start = time.time()

    basic_info = f"{target_age}/{target_sex}/{target_job}/{target_prefer}"
    

    if more_info is None:
        input_values = (product, basic_info)
    else:
        input_values = (product, basic_info, more_info)

    # print(basic_info)
    # print(input_values)

    result = gpt_input_values(input_values)
    # app.state.prompt_dalle = product+', '+', '.join(result['제품디자인'])+', product full shot'
    #달리에 보낼때 이런식으로 손 써줘야함
    
    end = time.time()

    print(f"{end - start:.5f} sec")

    print(result)

    if result == None:
        result = gpt_input_values(input_values)
    return result


# ---------------------완료-----------------------
# 타겟팅 - dalle-2 이미지 생성
@app.post('/targeting_create_image')
async def Targeting_Create_Image(
     user_id : int = Form(...),
     result : str = Form(...),
     product : str = Form(...)
    ):

    print("start to create image")

    # print(user_id)
    # print(result)
    # print(product)
    start = time.time()

    result = literal_eval(result)
    print(result['제품디자인'])

    if isinstance(result['제품디자인'], list):
        prompt_dalle = product+', '+', '.join(result['제품디자인'])+', product full shot'
    
    else:
        prompt_dalle = product + ', ' + result["제품디자인"] + ', product full shot'
    
    print(prompt_dalle)
    #달리에 보낼때 이런식으로 손 써줘야함
    img_url = use_dalle(prompt_dalle)

    end = time.time()
    print(f"dalle create : {end - start:.5f} sec")

    return {'img_url':img_url}


# @app.post('/aaaaaaaaaa')
# async def AAAAAAAAAA( 
#      more_info : Annotated[str,Form()] = None
#     ):
     
#      print(more_info)
#      print(more_info is None)

@app.post("/aaa")
async def AAA(result : str = Form(...)):
    print(result)
    return result


# ---------------------완료-----------------------
# 타겟팅 - 전체 데이터 저장
@app.post('/targeting_image_upload')
async def Targeting_Image_Upload(
     user_id : int = Form(...),
     target_sex : str = Form(...),
     target_age : str = Form(...),
     target_job : str = Form(...),
     target_prefer : str = Form(...),
     product : str = Form(...),
     more_info : Annotated[str,Form()] = None,
     img_title : str = Form(...),
     img_url : str = Form(...),
     img_idx : int = Form(...),
     result : str = Form(...)
    ):



    result = literal_eval(result)
    
    if len(result.keys()) == 3:
        Targeting_Info_columns = [user_id,target_sex,target_age,target_job,target_prefer,more_info,product,result['고객키워드'][0],result['고객키워드'][1],result['제품디자인'],result["디자인이유"],img_idx]
    else:
         Targeting_Info_columns = [user_id,target_sex,target_age,target_job,target_prefer,more_info,product,None,None,result['제품디자인'],result["디자인이유"],img_idx]
    

    
    with open('Targeting_Info.csv', mode='a', newline='') as f:
        csv_writer = csv.writer(f, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(Targeting_Info_columns)
        f.close()


    ################## url 들어가서 이미지 저장하고 firbase storage에 올리기 #########################
    # url로 이미지 저장
    urllib.request.urlretrieve(img_url, str(img_idx) + ".jpg")

    # /image => 저장 폴더
    # 뒤에 fileName이나 파일 이름
    blob = bucket.blob('image/' + str(img_idx) + '.jpg')

    # 로컬에 있는 파일
    blob.upload_from_filename(str(img_idx) + '.jpg')

    # Opt : if you want to make public access from the URL
    blob.make_public()

    public_url = blob.public_url
    print("your file url", public_url)

    #################################################################################################

    now = datetime.now()

    # 타겟팅에서 나온 이미지 정보
    Targeting_Image_Info_columns = [user_id,img_idx,img_title,public_url,now]
    with open('Targeting_Image_Info.csv', mode='a', newline='') as f:
        csv_writer = csv.writer(f, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(Targeting_Image_Info_columns)
        f.close()

    os.remove(f"{str(img_idx)}" + ".jpg")

    return {'result':"ok"}


# 
# 마이페이지 - 내가 생성, 내가 업로드한 사진 전부 받아오기
@app.post('/mypage_my_image')
async def Mypage_My_Image(
     user_id : int = Form(...),
    ):

    df = pd.read_csv("Targeting_Image_Info.csv")
    user_df = df[df["user_id"] == user_id].reset_index(drop=True)

    save_imgs_df = pd.read_csv("User_Save_Img.csv")
    save_cnt = literal_eval(save_imgs_df[save_imgs_df['user_id']==user_id]['save_img_idx_list'].values[0])

    targeting_df = pd.read_csv("Targeting_info.csv")


    # user_id의 모든 이미지 링크받아오기
    all_images = []
    for i in range(len(user_df)):
        # img_idx로 chatgpt_summary, chatgpt_reason 가져오기
        target_persona = targeting_df.loc[i,['target_sex','target_age','target_job','target_prefer']].values

        print(target_persona)
        
        persona_dict = {"persona" : f"{target_persona[0]}/{target_persona[1]}/{target_persona[2]}/{target_persona[3]}"}
        target_df = targeting_df[targeting_df['img_idx'] == df.loc[i,'img_idx']].reset_index(drop=True)
        target_dict = target_df.loc[0,['chatgpt_summary', 'chatgpt_reason']].to_dict()
        # target_dict['chatgpt_summary'] = literal_eval(target_dict['chatgpt_summary'])
        print(target_dict)

        # target_dict에 업데이트 시켜주기
        target_dict.update(df.loc[i,['img_idx','img_url','img_create_date']].to_dict())
        target_dict.update(persona_dict)

        all_images.append(target_dict)

    all_images = sorted(all_images, key=lambda x :x['img_create_date'], reverse=True)

    print(all_images)
    # print(len(all_images))
    # print(len(save_cnt))
    
    
    return {"result" : all_images,
            "create_imgs_cnt" : len(all_images),
            "save_imgs_cnt" : len(save_cnt)}





# ---------------------완료-----------------------
# 마이페이지 - 내가 저장한 사진 전부 받아오기
@app.post('/mypage_my_fork_image')
async def Mypage_My_Fork_Image(
     user_id : int = Form(...),
    ):

    df = pd.read_csv("User_Save_Img.csv")

    target_img_df = pd.read_csv("Targeting_Image_Info.csv")

    

    # 유저가 저장한 이미지의 idx 리스트 
    save_img_idx_list = literal_eval(df[df['user_id']==user_id]['save_img_idx_list'].values[0])
    print(save_img_idx_list)

    all_fork_images = []

    for i in save_img_idx_list:
        target_same_id_img_df = target_img_df[target_img_df['img_idx'] == i].reset_index(drop=True)

        for j in range(len(target_same_id_img_df)):
        
            target_same_id_img_dict = target_same_id_img_df.loc[j,['img_idx','img_url','img_create_date']].to_dict()
            all_fork_images.append(target_same_id_img_dict)

    print(all_fork_images)
    all_fork_images = sorted(all_fork_images, key=lambda x :x['img_create_date'], reverse=True)

    return {"result" : all_fork_images}

# ---------------------완료-----------------------
# 마이페이지 - 이미지 상세정보 : 상세 정보에서 비율 보기
@app.post('/mypage_image_detail_info')
async def mypage_Image_Detail_Info(
     user_id : int = Form(...),
     img_idx : int = Form(...)
     ):

    img_more_df = pd.read_csv("Image_More_Info.csv")

    user_df = pd.read_csv("User_Info.csv")

    # 이미지를 좋아한 사람들의 id 리스트
    user_liked_list = literal_eval(img_more_df[img_more_df['img_idx'] == img_idx]['img_liked_user_list'].values[0])

    # 좋아한 사람 수
    print("좋아한 사람 수 : ", len(user_liked_list))

    ########################## 남자, 여자 비율과 나이 비율 #################################

    prefer_dict = {}

    
    for i in user_liked_list:
        same_id_df = user_df[user_df['user_id'] == i]
        user_sex_age_prefer = list(same_id_df[['user_sex','user_age','user_prefer']].values[0])
        # print(user_sex_age_prefer)

        ### 선호 비율 구하기
        if user_sex_age_prefer[2] not in prefer_dict.keys():
            prefer_dict[user_sex_age_prefer[2]] = 1
        else :
            prefer_dict[user_sex_age_prefer[2]] += 1

    print(prefer_dict)

    ### prefer top3 추출
    sort_prefer = sorted(prefer_dict.items(), key=lambda x: x[1], reverse=True)[:3]
    prefer_result = []
    for x in sort_prefer:
        prefer_result.append({"prefer" : x[0],
                            "prefer_ratio" : str(round(x[1]/len(user_liked_list),2))+"%"})


    result = {
                "result" : prefer_result
    }

    return result