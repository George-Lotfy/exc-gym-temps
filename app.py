from flask import Flask, request, jsonify
import os
import requests
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

def generate_workout_sheets(text_data):
    gender = text_data.get('gender', 'male').lower()
    client_name = text_data.get('client_name', 'المشترك')
    exercises = text_data.get('exercises', [])
    
    # تحديد الصور والألوان الأساسية حسب نوع المشترك
    if gender == 'female':
        cover_path = "female_cover.png"
        table_1_path = "female_table_1.png"
        table_2_path = "female_table_2.png"
        table_4_path = "female_table_4.png"
        text_color = (139, 77, 75)  # اللون العنابي المتناسق مع الروز
    else:
        cover_path = "male_cover.png"
        table_1_path = "male_table_1.png"
        table_2_path = "male_table_2.png"
        table_4_path = "male_table_4.png"
        text_color = (255, 255, 255) # اللون الأبيض المتناسق مع الأزرق

    # تحميل الخط العربي
    font_path = "Cairo-Bold.ttf"
    if os.path.exists(font_path):
        title_font = ImageFont.truetype(font_path, size=40)
        body_font = ImageFont.truetype(font_path, size=24)
    else:
        title_font = body_font = ImageFont.load_default()

    generated_files = []

    # 1. توليد صفحة الغلاف أولاً باسم المشترك
    if os.path.exists(cover_path):
        cover_img = Image.open(cover_path)
        draw_cover = ImageDraw.Draw(cover_img)
        draw_cover.text((300, 850), f"اللاعب: {client_name}", fill=text_color, font=title_font)
        cover_out = "out_cover.png"
        cover_img.save(cover_out, "PNG", quality=100)
        generated_files.append(cover_out)

    if not exercises:
        return generated_files

    # 2. فحص عدد التمارين واختيار الجدول المناسب ذكياً
    total_exercises = len(exercises)
    pages = []
    
    if total_exercises == 1:
        # لو تمرين واحد، ياخد جدول الصف الواحد
        pages.append({'template': table_1_path, 'data': exercises})
    elif total_exercises == 2:
        # لو تمرينين، ياخد جدول الصفين
        pages.append({'template': table_2_path, 'data': exercises})
    else:
        # لو من 3 لـ 4 تمارين (أو أكتر)، بنستخدم جدول الـ 4 صفوف ونقسمهم صفحات لو زادوا عن 4
        for i in range(0, total_exercises, 4):
            pages.append({'template': table_4_path, 'data': exercises[i:i+4]})

    # 3. رص البيانات داخل الجداول المحددة
    for page_idx, page in enumerate(pages):
        template_file = page['template']
        if not os.path.exists(template_file):
            continue
            
        img = Image.open(template_file)
        draw = ImageDraw.Draw(img)
        
        # طباعة اسم المشترك ورقم الصفحة في الأعلى
        draw.text((80, 50), f"اللاعب: {client_name} (صفحة {page_idx + 1})", fill=text_color, font=body_font)
        
        # أبعاد خانات الأعمدة (من اليمين للشمال)
        col_exercise_x = 720  # اسم التمرين
        col_sets_x = 240      # المجموعات
        col_reps_x = 360      # العدات
        col_rest_x = 460      # الراحة
        
        start_y = 220  # نقطة البداية الرأسية لأول سطر تمرين
        row_height = 70 # الارتفاع بين السطر والتاني
        
        for idx, ex in enumerate(page['data']):
            current_y = start_y + (idx * row_height)
                
            draw.text((col_exercise_x, current_y), ex.get('name', ''), fill=text_color, font=body_font)
            draw.text((col_sets_x, current_y), str(ex.get('sets', '')), fill=text_color, font=body_font)
            draw.text((col_reps_x, current_y), str(ex.get('reps', '')), fill=text_color, font=body_font)
            draw.text((col_rest_x, current_y), ex.get('rest', ''), fill=text_color, font=body_font)
            
        page_out = f"out_table_page_{page_idx + 1}.png"
        img.save(page_out, "PNG", quality=100)
        generated_files.append(page_out)

    return generated_files

def upload_to_imgbb(image_path):
    api_key = "6bc99df9a79fa4bb66bd434b9dfb219f"
    with open(image_path, "rb") as file:
        payload = {"key": api_key}
        files = {"image": file}
        response = requests.post("https://api.imgbb.com/1/upload", data=payload, files=files)
        return response.json()['data']['url']

@app.route('/process-workout', methods=['POST'])
def process_workout():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400
        
    img_paths = generate_workout_sheets(data)
    if img_paths:
        urls = [upload_to_imgbb(path) for path in img_paths]
        return jsonify({"image_urls": urls}), 200
        
    return jsonify({"error": "Failed to generate images"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))