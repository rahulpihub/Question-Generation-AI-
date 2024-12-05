from django.shortcuts import render
import csv
import os
import google.generativeai as genai
from django.conf import settings
from django.http import HttpResponse
from urllib.parse import quote

# Configure Gemini API
model = genai.GenerativeModel('gemini-1.5-pro-latest')
api_key = "AIzaSyDBrlXjAV-LLGc4AWqE8thsmhJioqCLK9E"  # Ensure this API key is secure
genai.configure(api_key=api_key)

# Set the output directory for CSV
output_dir = settings.OUTPUT_DIR
# Ensure the directory exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

def generate_questions(request):
    if request.method == "POST":
        # Getting form data
        topic = request.POST.get("topic")
        subtopic = request.POST.get("subtopic")
        level = request.POST.get("level")
        question_type = request.POST.get("question_type")
        num_questions_input = request.POST.get("num_questions")

        num_questions = None
        try:
            num_questions = int(num_questions_input)  # Convert the input to an integer
        except ValueError:
            return render(request, "generator/index.html", {"error": "Please enter a valid number for the number of questions."})

        if num_questions:
            # Define the prompt and CSV columns based on question type
            prompt = ""
            csv_columns = []

            if question_type == "Fill Ups":
                prompt = (
                    f"Generate {num_questions} {question_type} questions "
                    f"on the topic '{topic}' with subtopic '{subtopic}' "
                    f"for a {level} level audience. "
                    f"Return the questions in the format i dont any other unwanted informationlike ''' from the initial : \n\n"
                    f"Question: <The generated question>\n"
                    f"Answer: <The correct answer>"
                )
                csv_columns = ["Topic", "Subtopic", "Level", "Question Type", "Question", "Answer"]
            elif question_type == "True-False":
                prompt = (
                    f"Generate {num_questions} {question_type} questions "
                    f"on the topic '{topic}' with subtopic '{subtopic}' "
                    f"for a {level} level audience. "
                    f"Return the questions with the Questions : and its Answer : check the below format ensure that the question and answer generated in the below format only \n\n"
                    f"Question: <The generated question>\n"
                    f"Answer: <The correct answer>"
                )
                csv_columns = ["Topic", "Subtopic", "Level", "Question Type", "Question", "Answer"]
            else:  # Multiple Choice Questions
                prompt = (
                    f"Generate {num_questions} {question_type} questions "
                    f"on the topic '{topic}' with subtopic '{subtopic}' "
                    f"for a {level} level audience. "
                    f"Return the questions in the format i dont any other unwanted information  ''' from the initial : \n\n"
                    f"Question: <The generated question>\n"
                    f"Options: <A list of options separated by commas>\n"
                    f"Answer: <The correct answer>"
                )
                csv_columns = ["Topic", "Subtopic", "Level", "Question Type", "Question", "Option 1", "Option 2", "Option 3", "Option 4", "Answer"]

            try:
                # Request to Gemini AI (Google Generative AI)
                response = model.generate_content(prompt)

                # Extract the text content from the response
                question_text = response._result.candidates[0].content.parts[0].text

                # Check if the response is empty or malformed
                if not question_text.strip():
                    return render(request, "generator/index.html", {"error": "No questions generated. Please try again."})

                questions_list = question_text.strip().split("\n\n")  # Split questions by newlines

                # Ensure the question type is valid for filenames
                safe_question_type = question_type.replace("/", "_")  # Replace '/' with '_'

                # Save the questions to CSV
                csv_file_path = os.path.join(output_dir, f"generated_questions_{safe_question_type}.csv")
                csv_file_name = f"generated_questions_{question_type.replace('/', '_')}.csv"
                csv_file_name = os.path.basename(csv_file_path)

                # Print to verify the path
                print(f"CSV File Path: {csv_file_path}")

                with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)

                    # Write the header
                    writer.writerow(csv_columns)

                    for question in questions_list:
                        lines = question.split("\n")
                        question_text = lines[0].strip().replace("Question:", "").strip()

                        if question_type == "Fill Ups":
                            answer_text = lines[1].replace("Answer: ", "").strip()
                            writer.writerow([topic, subtopic, level, question_type, question_text, answer_text])
                        elif question_type == "True/False":
                            answer_text = lines[1].replace("Answer: ", "").strip()
                            writer.writerow([topic, subtopic, level, question_type, question_text, answer_text])
                        else:
                            options_text = lines[1].replace("Options: ", "").strip()
                            options = options_text.split(",")  # Split options by commas
                            options = options + [""] * (4 - len(options))  # Ensure we have 4 options
                            answer_text = lines[2].replace("Answer: ", "").strip()
                            writer.writerow([topic, subtopic, level, question_type, question_text, *options, answer_text])

                # Return a response indicating success and the path for download
                return render(request, "generator/index.html", {
                    "success": f"Questions saved to {csv_file_path}",
                    "questions": questions_list,
                    "csv_file_name": csv_file_name  # Pass only the file name
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
