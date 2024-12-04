from django.shortcuts import render
import csv
import os
import google.generativeai as genai
from django.conf import settings
from django.http import HttpResponse
from urllib.parse import quote


# Configure Gemini API
model = genai.GenerativeModel('gemini-1.5-pro-latest')
api_key = "AIzaSyDBrlXjAV-LLGc4AWqE8thsmhJioqCLK9E"
genai.configure(api_key=api_key)

# Set the output directory for CSV
output_dir = settings.OUTPUT_DIR
os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

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
                    f"Return the questions in the format for the Answers I don't want any explanation, I need only the answer: \n\n"
                    f"Question: <The generated question>\n"
                    f"Answer: <The correct answer>"
                )
                csv_columns = ["Topic", "Subtopic", "Level", "Question Type", "Question", "Answer"]
            elif question_type == "True/False":
                prompt = (
                    f"Generate {num_questions} {question_type} questions "
                    f"on the topic '{topic}' with subtopic '{subtopic}' "
                    f"for a {level} level audience. "
                    f"Return the questions in the format for the Answers I don't want any explanation, I need only the answer whether it is true or false: \n\n"
                    f"Question: <The generated question>\n"
                    f"Answer: <The correct answer>"
                )
                csv_columns = ["Topic", "Subtopic", "Level", "Question Type", "Question", "Answer"]
            else:
                prompt = (
                    f"Generate {num_questions} {question_type} questions "
                    f"on the topic '{topic}' with subtopic '{subtopic}' "
                    f"for a {level} level audience. "
                    f"Return the questions with by not mentioning the 1.) ,2.) and Question in it"
                    f"Question: <The generated question>\n"
                    f"Options: <A list of options separated by commas>\n"
                    f"Answer: <The correct answer>"
                )
                csv_columns = ["Topic", "Subtopic", "Level", "Question Type", "Question", "Options one", "Options two", "Options three", "Options four", "Answer"]

            try:
                # Request to Gemini AI (Google Generative AI)
                response = model.generate_content(prompt)

                # Extract the text content from the response
                question_text = response._result.candidates[0].content.parts[0].text

                questions_list = question_text.strip().split("\n\n")  # Split questions by newlines
                if len(questions_list) < num_questions:
                    error_message = f"Only {len(questions_list)} questions were generated, which is less than the requested {num_questions}."
                    return render(request, "generator/index.html", {"error": error_message})

                # Save the questions to CSV
                csv_file_path = os.path.join(output_dir, f"generated_questions_{question_type}.csv")

                with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)

                    # Write the header
                    writer.writerow(csv_columns)

                    for question in questions_list:
                        lines = question.split("\n")
                        question_text = lines[0].strip()
                        if question_text.startswith("Question:"):
                            question_text = question_text.replace("Question:", "").strip()  # Remove "Question: "

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
                    "csv_file_path": csv_file_path  # Pass the path to the template
                })
            except Exception as e:
                return render(request, "generator/index.html", {"error": f"Error generating questions: {str(e)}"})
        else:
            return render(request, "generator/index.html", {"error": "Please enter a valid number for the number of questions."})
    return render(request, "generator/index.html")

def download_csv(request, file_name):
    # Path to the directory where your CSV file is stored
    directory = 'D:\\Rahul\\Work\\Dec\\3-12-2024\\question_generator\\Question-Generation-AI-\\output'
    file_path = os.path.join(directory, file_name)

    if os.path.exists(file_path):
        # Open the file and return it as an HTTP response
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/csv')
            response['Content-Disposition'] = f'attachment; filename={file_name}'
            return response
    else:
        # If the file doesn't exist, return an error message
        return HttpResponse("File not found", status=404)