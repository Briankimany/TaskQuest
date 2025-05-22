
from flask import Blueprint, render_template, request
import json
import os
from app.config import app_folder

assistant = Blueprint('assistant', __name__)

@assistant.route('/penalty-results')
def penalty_results():
    result_path = app_folder /'test/penalty_results_all_models.json'

    try:
        with open(result_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return f"Error loading results: {str(e)}", 500

    model_names = list(data.keys())
    page = int(request.args.get('page', 1))
    per_page = 1  # show one model at a time

    total_pages = len(model_names)
    current_model = model_names[page - 1]
    model_data = data[current_model]

    return render_template(
        'penalties_results.html',
        model_name=current_model,
        model_data=model_data,
        page=page,
        total_pages=total_pages
    )
