from django.shortcuts import render ,redirect
import csv
import os
from datetime import datetime
import google.generativeai as genai
from django.conf import settings
from django.http import HttpResponse
from urllib.parse import quote
from django.http import JsonResponse
from .models import Question  # Import the model

# Define the API keys
apione = "AIzaSyDUZjA_bSO8YT0fkSEAPudyc_Kd0ew5YvM"
apitwo = "AIzaSyA4PwhxtBusjL-uPR16exclcuNBykQcdTA"

# Configure the output directory for CSV
output_dir = settings.OUTPUT_DIR
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

def generate_questions(request):
    if request.method == "POST":
        # Getting form data
        topic = request.POST.get("topic", "").strip()
        subtopic = request.POST.get("subtopic", "").strip()
        level = request.POST.get("level", "").strip()
        question_type = request.POST.get("question_type", "").strip()
        num_questions_input = request.POST.get("num_questions", "").strip()

        # Normalize question type for validation
        question_type_mapping = {
            "fill ups": "Fill Ups",
            "true/false": "True/False",
            "multiple choice": "Multiple Choice",
        }
        question_type_key = question_type.lower()
        question_type = question_type_mapping.get(question_type_key)

        if not question_type:
            return render(request, "generator/index.html", {"error": "Invalid question type selected. Please try again."})

        # Validate the number of questions
        try:
            num_questions = int(num_questions_input)
        except ValueError:
            return render(request, "generator/index.html", {"error": "Please enter a valid number for the number of questions."})

        # Split the number of questions into two halves
        half1 = num_questions // 2
        half2 = num_questions - half1

        # Generate prompts
        prompt_template = {
            "Fill Ups": (
                f"Generate {{count}} Fill Ups questions on the topic '{topic}' with subtopic '{subtopic}' "
                f"for a {level} level audience. Return the questions in the format:\n\n"
                f"The generated questions should not have the 1.,2.,3. this like pointing numbers in the first\n"
                f"Question: <The generated question>\n"
                f"Answer: <The correct answer>"
            ),
            "True/False": (
                f"Generate {{count}} True/False questions on the topic '{topic}' with subtopic '{subtopic}' "
                f"for a {level} level audience. Return the questions in the format:\n\n"
                f"The generated questions should not have the 1.,2.,3. this like pointing numbers in the first\n"
                f"Question: <The generated question>\n"
                f"Answer: <True/False>"
            ),
            "Multiple Choice": (
                f"Generate {{count}} Multiple Choice Questions on the topic '{topic}' with subtopic '{subtopic}' "
                f"for a {level} level audience. Ensure that you have mentioned numbers for every generated questions .Return the questions in the format:\n\n"
                f"The generated questions should not have the 1.,2.,3. this like pointing numbers in the first\n"
                f"Question: <The generated question>\n"
                f"Options: <Comma-separated options>\n"
                f"Answer: <The correct answer>"
            )
        }

        prompt = prompt_template.get(question_type, "")
        csv_columns = (
            ["Topic", "Subtopic", "Level", "Question Type", "Question", "Answer"]
            if question_type in ["Fill Ups", "True/False"]
            else ["Topic", "Subtopic", "Level", "Question Type", "Question", "Option 1", "Option 2", "Option 3", "Option 4", "Answer"]
        )

        questions_list = []

        try:
            # First half using API key one
            genai.configure(api_key=apione)
            prompt_half1 = prompt.replace("{count}", str(half1))
            response1 = genai.GenerativeModel("gemini-1.5-pro-latest").generate_content(prompt_half1)
            questions_list.extend(response1._result.candidates[0].content.parts[0].text.strip().split("\n\n"))

            # Second half using API key two
            genai.configure(api_key=apitwo)
            prompt_half2 = prompt.replace("{count}", str(half2))
            response2 = genai.GenerativeModel("gemini-1.5-pro-latest").generate_content(prompt_half2)
            questions_list.extend(response2._result.candidates[0].content.parts[0].text.strip().split("\n\n"))

            # Ensure the question type is valid for filenames
            safe_question_type = question_type.replace("/", "_")  # Replace '/' with '_'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file_path = os.path.join(output_dir, f"generated_questions_{safe_question_type}_{timestamp}.csv")
            csv_file_name = os.path.basename(csv_file_path)

            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(csv_columns)

                for question in questions_list:
                    lines = question.split("\n")
                    question_text = lines[0].replace("Question:", "").strip()

                    if question_type == "Fill Ups":
                        answer_text = lines[1].replace("Answer:", "").strip()
                        Question.objects.create(
                            topic=topic,
                            subtopic=subtopic,
                            level=level,
                            question_type=question_type,
                            question=question_text,
                            answer=answer_text
                        )
                        writer.writerow([topic, subtopic, level, question_type, question_text, answer_text])
                    elif question_type == "True/False":
                        answer_text = lines[1].replace("Answer:", "").strip()
                        Question.objects.create(
                            topic=topic,
                            subtopic=subtopic,
                            level=level,
                            question_type=question_type,
                            question=question_text,
                            answer=answer_text
                        )
                        writer.writerow([topic, subtopic, level, question_type, question_text, answer_text])
                    else:  # Multiple Choice Questions
                        options_text = lines[1].replace("Options:", "").strip()
                        options = options_text.split(",")
                        options = options + [""] * (4 - len(options))  # Ensure 4 options
                        answer_text = lines[2].replace("Answer:", "").strip()
                        Question.objects.create(
                            topic=topic,
                            subtopic=subtopic,
                            level=level,
                            question_type=question_type,
                            question=question_text,
                            option_1=options[0],
                            option_2=options[1],
                            option_3=options[2],
                            option_4=options[3],
                            answer=answer_text
                        )
                        writer.writerow([topic, subtopic, level, question_type, question_text, *options, answer_text])

            return render(request, "generator/index.html", {
                "success": f"Questions saved to {csv_file_path}",
                "questions": questions_list,
                "csv_file_name": csv_file_name
            })

        except Exception as e:
            return render(request, "generator/index.html", {"error": f"Error generating questions: {str(e)}"})

    return render(request, "generator/index.html")


def download_csv(request, file_name):
    try:
        # Ensure the file exists
        file_path = os.path.join(settings.OUTPUT_DIR, file_name)
        if not os.path.exists(file_path):
            return HttpResponse("File not found.", status=404)

        # Serve the file for download
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/csv')
            response['Content-Disposition'] = f'attachment; filename={quote(file_name)}'
            return response
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


def view_questions(request, csv_file_name):
    try:
        # Get the file path
        file_path = os.path.join(settings.OUTPUT_DIR, csv_file_name)

        if not os.path.exists(file_path):
            return HttpResponse("File not found.", status=404)

        # Read the CSV file
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            rows = list(reader)

        # First row is the header
        columns = rows[0]
        data = rows[1:]

        # Pass the data to the template
        return render(request, "generator/view_questions.html", {
            "columns": columns,
            "data": data,
            "csv_file_name": csv_file_name
        })
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
    
from django.shortcuts import render
from django.http import HttpResponse
import csv
import os
from django.conf import settings

def edit_questions(request, csv_file_name):
    try:
        file_path = os.path.join(settings.OUTPUT_DIR, csv_file_name)

        if not os.path.exists(file_path):
            return HttpResponse("File not found.", status=404)

        # Read the CSV file
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            rows = list(reader)

        # Define the columns we expect to see
        expected_columns = ["Question", "Option 1", "Option 2", "Option 3", "Option 4", "Answer"]

        # The first row contains column names
        columns = rows[0]

        # Filter out columns that are not in the expected ones
        filtered_columns = [col for col in expected_columns if col in columns]

        # Data is the remaining rows
        data = rows[1:]

        # Map the rows to the filtered columns and calculate the indexes
        mapped_data = []
        for i, row in enumerate(data):
            mapped_row = []
            for j, col in enumerate(filtered_columns):
                mapped_row.append({
                    'value': row[columns.index(col)] if col in columns else '',
                    'row_index': i + 1,
                    'col_index': j + 1
                })
            mapped_data.append(mapped_row)

        if request.method == "POST":
            # Handle insert row
            insert_row = request.POST.get('insert_row')
            if insert_row == 'true':
                mapped_data.append([{
                    'value': '',
                    'row_index': len(mapped_data) + 1,
                    'col_index': j + 1
                } for j in range(len(filtered_columns))])

            # Handle delete row
            delete_row_index = request.POST.get('delete_row')
            if delete_row_index:
                delete_row_index = int(delete_row_index)
                mapped_data = [row for i, row in enumerate(mapped_data) if i != delete_row_index]

            # Process updated CSV data from the POST request
            updated_data = []
            for i, row in enumerate(mapped_data):
                updated_row = []
                for j, cell in enumerate(row):
                    updated_value = request.POST.get(f"cell_{cell['row_index']}_{cell['col_index']}")
                    updated_row.append(updated_value if updated_value else cell['value'])
                updated_data.append(updated_row)

            # Save updated data back to the CSV
            with open(file_path, mode="w", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(filtered_columns)
                writer.writerows(updated_data)

            # Don't redirect immediately, stay on the current page
            return render(request, "generator/edit_questions.html", {
                "columns": filtered_columns,
                "data": mapped_data,
                "csv_file_name": csv_file_name
            })

        # Render the edit page initially or after POST (to show the updates)
        return render(request, "generator/edit_questions.html", {
            "columns": filtered_columns,
            "data": mapped_data,
            "csv_file_name": csv_file_name
        })

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


def use_questions(request, csv_file_name):
    try:
        # Get the file path
        file_path = os.path.join(settings.OUTPUT_DIR, csv_file_name)

        if not os.path.exists(file_path):
            return HttpResponse("File not found.", status=404)

        # Read the CSV file
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            rows = list(reader)

        # Extract the columns and data
        columns = rows[0]
        data = rows[1:]

        # Get indices of relevant columns: "Question", "Option 1", "Option 2", "Option 3", "Option 4", and "Answer"
        question_index = columns.index("Question")
        answer_index = columns.index("Answer")

        # Try to extract the options, defaulting to None if not found
        option_indices = []
        for i in range(1, 5):  # For Option 1, Option 2, Option 3, Option 4
            try:
                option_indices.append(columns.index(f"Option {i}"))
            except ValueError:
                option_indices.append(None)

        filtered_data = []
        for row in data:
            # Prepare the options list, skipping None values
            options = [row[i] if i is not None else "N/A" for i in option_indices]
            filtered_data.append({
                "question": row[question_index],
                "options": options,
                "answer": row[answer_index]
            })

        # If it's an AJAX request for a specific question
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            question_index = int(request.GET.get('index', 0))
            if 0 <= question_index < len(filtered_data):
                return JsonResponse({
                    "question": filtered_data[question_index]["question"],
                    "options": filtered_data[question_index]["options"],
                    "answer": filtered_data[question_index]["answer"]
                })
            return JsonResponse({"error": "Index out of range"}, status=400)

        # Count the number of questions
        question_count = len(filtered_data)

        # Pass the filtered data and question count to the template
        return render(request, "generator/use_questions.html", {
            "data": filtered_data,
            "csv_file_name": csv_file_name,
            "question_count": question_count,
        })
    except ValueError:
        return HttpResponse("The CSV file does not have the necessary columns.", status=400)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
