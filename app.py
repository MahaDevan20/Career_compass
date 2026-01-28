import os
import io
import traceback
from flask import Flask, render_template, request, send_file
import google.generativeai as genai
from xhtml2pdf import pisa
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# Initialize Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("No GEMINI_API_KEY found in environment variables. Please check your .env file.")

genai.configure(api_key=api_key)

# Create a model instance
model = genai.GenerativeModel("models/gemini-flash-latest")

def generate_recommendations(user_data):
    """Generate career recommendations based on user data using Gemini AI"""
    try:
        if user_data['goal'] == "Higher Studies":
            prompt = f"""
            Act as a career counselor specializing in higher education. Provide 3 detailed recommendations for {user_data['name']} based on:
            - Age: {user_data['age']}
            - Qualifications: {user_data['qualifications']}
            - Skills: {user_data['skills']}
            - Interests: {user_data['interests']}
            - Location: {user_data['location']}
            
            For each recommendation, provide this exact format:
            --- RECOMMENDATION 1
            TITLE: [Recommendation title]
            OVERVIEW: [Brief overview]
            DETAILS: [Detailed description]
            PROS: [comma, separated, list]
            CONS: [comma, separated, list]
            INSTITUTIONS: [comma, separated, list of top institutions]
            RESOURCES: [comma, separated, list of resources]
            """
        else:
            prompt = f"""
            Act as a career counselor specializing in job placements. Provide 3 detailed career recommendations for {user_data['name']} based on:
            - Age: {user_data['age']}
            - Qualifications: {user_data['qualifications']}
            - Skills: {user_data['skills']}
            - Interests: {user_data['interests']}
            - Location: {user_data['location']}
            
            For each recommendation, provide this exact format:
            --- RECOMMENDATION 1
            TITLE: [Job title/role]
            OVERVIEW: [Brief overview]
            DETAILS: [Detailed description]
            PROS: [comma, separated, list]
            CONS: [comma, separated, list]
            COMPANIES: [comma, separated, list of top companies]
            SALARY: [Salary range]
            GROWTH: [Growth potential]
            SKILLS NEEDED: [comma, separated, list]
            RESOURCES: [comma, separated, list of resources]
            """
        
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        print(f"Generation error: {str(e)}")
        traceback.print_exc()
        return None

def parse_recommendations(text_response, is_higher_study):
    """Parse the text response into structured recommendation data"""
    recommendations = []
    # Split by any variation of RECOMMENDATION section header
    sections = text_response.split('--- RECOMMENDATION')
    if len(sections) <= 1:
        # Fallback if the format is slightly different
        sections = text_response.split('RECOMMENDATION')
    
    sections = sections[1:] # Skip preamble
    
    for section in sections:
        rec = {}
        # Simple extraction using line containment
        lines = [l.strip() for l in section.split('\n') if l.strip()]
        
        for line in lines:
            clean_line = line.replace('**', '').replace('*', '').strip()
            if 'TITLE:' in clean_line:
                rec['title'] = clean_line.split('TITLE:')[1].strip()
            elif 'OVERVIEW:' in clean_line:
                rec['overview'] = clean_line.split('OVERVIEW:')[1].strip()
            elif 'DETAILS:' in clean_line:
                rec['details'] = clean_line.split('DETAILS:')[1].strip()
            elif 'PROS:' in clean_line:
                content = clean_line.split('PROS:')[1].strip('[] ').split(',')
                rec['pros'] = [x.strip() for x in content if x.strip()]
            elif 'CONS:' in clean_line:
                content = clean_line.split('CONS:')[1].strip('[] ').split(',')
                rec['cons'] = [x.strip() for x in content if x.strip()]
            elif 'RESOURCES:' in clean_line:
                content = clean_line.split('RESOURCES:')[1].strip('[] ').split(',')
                rec['resources'] = [x.strip() for x in content if x.strip()]
            elif is_higher_study:
                if 'INSTITUTIONS:' in clean_line:
                    content = clean_line.split('INSTITUTIONS:')[1].strip('[] ').split(',')
                    rec['institutions'] = [x.strip() for x in content if x.strip()]
            else:
                if 'COMPANIES:' in clean_line:
                    content = clean_line.split('COMPANIES:')[1].strip('[] ').split(',')
                    rec['companies'] = [x.strip() for x in content if x.strip()]
                elif 'SALARY:' in clean_line:
                    rec['salary_range'] = clean_line.split('SALARY:')[1].strip()
                elif 'GROWTH:' in clean_line:
                    rec['growth'] = clean_line.split('GROWTH:')[1].strip()
                elif 'SKILLS NEEDED:' in clean_line:
                    content = clean_line.split('SKILLS NEEDED:')[1].strip('[] ').split(',')
                    rec['skills_needed'] = [x.strip() for x in content if x.strip()]
        
        if rec.get('title'):
            # Fill in defaults for missing fields to prevent UI errors
            rec.setdefault('overview', 'No overview provided.')
            rec.setdefault('details', 'No details provided.')
            rec.setdefault('pros', [])
            rec.setdefault('cons', [])
            rec.setdefault('resources', [])
            if is_higher_study:
                rec.setdefault('institutions', [])
            else:
                rec.setdefault('companies', [])
                rec.setdefault('salary_range', 'N/A')
                rec.setdefault('growth', 'N/A')
                rec.setdefault('skills_needed', [])
            recommendations.append(rec)
    
    return recommendations

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_data = {
            'name': request.form.get('name'),
            'age': request.form.get('age'),
            'qualifications': request.form.get('qualifications'),
            'skills': request.form.get('skills'),
            'interests': request.form.get('interests'),
            'location': request.form.get('location'),
            'goal': request.form.get('goal')
        }
        return render_template('loading.html', user_data=user_data)
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        user_data = {
            'name': request.form.get('name'),
            'age': request.form.get('age'),
            'qualifications': request.form.get('qualifications'),
            'skills': request.form.get('skills'),
            'interests': request.form.get('interests'),
            'location': request.form.get('location'),
            'goal': request.form.get('goal')
        }
        
        # Generate recommendations
        response_text = generate_recommendations(user_data)
        if not response_text:
            raise ValueError("Failed to generate recommendations")
        
        # Parse recommendations
        is_higher_study = user_data['goal'] == "Higher Studies"
        recommendations = parse_recommendations(response_text, is_higher_study)
        
        return render_template('results.html', 
                            user_data=user_data,
                            recommendations=recommendations)
    
    except Exception as e:
        print(f"Route /generate error: {str(e)}")
        traceback.print_exc()
        return render_template('error.html',
                            error="Couldn't generate recommendations. Please try again.")

@app.route('/recommendation_detail', methods=['POST'])
def recommendation_detail():
    try:
        index = int(request.form.get('index', 0))
        if index < 0 or index > 2:
            raise ValueError("Invalid recommendation index")
        
        recommendations = []
        for i in range(3):
            rec = {
                'title': request.form.get(f'rec_{i}_title', ''),
                'overview': request.form.get(f'rec_{i}_overview', ''),
                'details': request.form.get(f'rec_{i}_details', ''),
                'pros': request.form.get(f'rec_{i}_pros', '').split('|'),
                'cons': request.form.get(f'rec_{i}_cons', '').split('|'),
                'resources': request.form.get(f'rec_{i}_resources', '').split('|')
            }
            
            if request.form.get('goal') == "Higher Studies":
                rec['institutions'] = request.form.get(f'rec_{i}_institutions', '').split('|')
            else:
                rec['companies'] = request.form.get(f'rec_{i}_companies', '').split('|')
                rec['salary_range'] = request.form.get(f'rec_{i}_salary', 'Not specified')
                rec['growth'] = request.form.get(f'rec_{i}_growth', 'Not specified')
                rec['skills_needed'] = request.form.get(f'rec_{i}_skills_needed', '').split('|')
            
            recommendations.append(rec)
        
        if not recommendations or not recommendations[0]['title']:
            raise ValueError("No recommendation data found")
        
        user_data = {
            'name': request.form.get('name', ''),
            'age': request.form.get('age', ''),
            'qualifications': request.form.get('qualifications', ''),
            'skills': request.form.get('skills', ''),
            'interests': request.form.get('interests', ''),
            'location': request.form.get('location', ''),
            'goal': request.form.get('goal', '')
        }
        
        return render_template('detail.html',
                       recommendations=recommendations,
                       user_data=user_data,
                       index=index)

    except Exception as e:
        print(f"Route /recommendation_detail error: {str(e)}")
        traceback.print_exc()
        return render_template('error.html',
                            error="Couldn't load recommendation details. Please try again from the beginning.")

@app.route('/download_report', methods=['POST'])
def download_report():
    try:
        user_data = {
            'name': request.form.get('name'),
            'age': request.form.get('age'),
            'qualifications': request.form.get('qualifications'),
            'skills': request.form.get('skills'),
            'interests': request.form.get('interests'),
            'location': request.form.get('location'),
            'goal': request.form.get('goal')
        }
        
        recommendations = []
        for i in range(3):
            title = request.form.get(f'rec_{i}_title')
            if not title:
                continue
            
            rec = {
                'title': title,
                'overview': request.form.get(f'rec_{i}_overview'),
                'details': request.form.get(f'rec_{i}_details')
            }

            if user_data['goal'] == "Higher Studies":
                inst = request.form.get(f'rec_{i}_institutions', '')
                rec['institutions'] = inst.split('|') if inst else []
            else:
                comp = request.form.get(f'rec_{i}_companies', '')
                rec['companies'] = comp.split('|') if comp else []
                rec['salary_range'] = request.form.get(f'rec_{i}_salary', 'N/A')
                rec['growth'] = request.form.get(f'rec_{i}_growth', 'N/A')

            recommendations.append(rec)
        
        # Enhanced HTML content for PDF
        html_content = f"""
        <html>
        <head>
            <style>
                @page {{ size: A4; margin: 1cm; }}
                body {{ font-family: 'Helvetica', 'Arial', sans-serif; color: #333; line-height: 1.5; }}
                .header {{ background-color: #4361ee; color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
                .header h1 {{ margin: 0; font-size: 28pt; }}
                .header p {{ margin: 5px 0 0; opacity: 0.9; }}
                .profile-section {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; border-left: 5px solid #4361ee; }}
                .profile-item {{ margin-bottom: 8px; font-size: 11pt; }}
                .profile-item strong {{ color: #4361ee; width: 150px; display: inline-block; }}
                .rec-card {{ border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 25px; padding: 20px; }}
                .rec-title {{ color: #4361ee; font-size: 18pt; margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                .section-label {{ font-weight: bold; color: #3f37c9; margin-top: 15px; display: block; text-transform: uppercase; font-size: 9pt; letter-spacing: 1px; }}
                .content-text {{ margin: 5px 0 15px; font-size: 11pt; text-align: justify; }}
                .tag-container {{ margin: 10px 0; }}
                .tag {{ background-color: #e9ecef; padding: 3px 10px; border-radius: 15px; font-size: 9pt; display: inline-block; margin-right: 5px; margin-bottom: 5px; color: #495057; }}
                .footer {{ text-align: center; color: #999; font-size: 9pt; margin-top: 50px; border-top: 1px solid #eee; padding-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Career Compass Report</h1>
                <p>Personalized Recommendations for {user_data['name']}</p>
            </div>

            <div class="profile-section">
                <div class="profile-item"><strong>Age:</strong> {user_data['age']}</div>
                <div class="profile-item"><strong>Qualifications:</strong> {user_data['qualifications']}</div>
                <div class="profile-item"><strong>Skills:</strong> {user_data['skills']}</div>
                <div class="profile-item"><strong>Interests:</strong> {user_data['interests']}</div>
                <div class="profile-item"><strong>Desired Location:</strong> {user_data['location']}</div>
                <div class="profile-item"><strong>Primary Goal:</strong> {user_data['goal']}</div>
            </div>

            <h2 style="color: #4361ee; margin-bottom: 20px;">Top Career Recommendations</h2>
        """

        for rec in recommendations:
            html_content += f"""
            <div class="rec-card">
                <h3 class="rec-title">{rec['title']}</h3>
                <span class="section-label">Overview</span>
                <p class="content-text">{rec['overview']}</p>
                
                <span class="section-label">Detailed Path</span>
                <p class="content-text">{rec['details']}</p>
            """
            
            if user_data['goal'] == "Higher Studies":
                html_content += '<span class="section-label">Top Institutions</span><div class="tag-container">'
                for inst in rec['institutions']:
                    html_content += f'<span class="tag">{inst}</span>'
                html_content += '</div>'
            else:
                html_content += '<span class="section-label">Target Companies</span><div class="tag-container">'
                for comp in rec['companies']:
                    html_content += f'<span class="tag">{comp}</span>'
                html_content += f'</div><p class="profile-item"><strong>Expected Salary:</strong> {rec["salary_range"]}</p>'
                html_content += f'<p class="profile-item"><strong>Growth Potential:</strong> {rec["growth"]}</p>'
                
            html_content += "</div>"

        html_content += """
            <div class="footer">
                Generated by Career Compass AI &bull; Empowering Your Professional Journey
            </div>
        </body></html>
        """

        pdf_file = io.BytesIO()
        pisa.CreatePDF(html_content, dest=pdf_file)
        pdf_file.seek(0)
        return send_file(pdf_file, download_name=f"Career_Report_{user_data['name'].replace(' ', '_')}.pdf", as_attachment=True, mimetype='application/pdf')
    except Exception as e:
        print("Download error:", e)
        return "An error occurred during PDF generation", 500

@app.route('/download_detailed_report', methods=['POST'])
def download_detailed_report():
    try:
        user_data = {
            'name': request.form.get('name'),
            'age': request.form.get('age'),
            'qualifications': request.form.get('qualifications'),
            'skills': request.form.get('skills'),
            'interests': request.form.get('interests'),
            'location': request.form.get('location'),
            'goal': request.form.get('goal')
        }

        rec = {
            'title': request.form.get('rec_0_title'),
            'overview': request.form.get('rec_0_overview'),
            'details': request.form.get('rec_0_details'),
            'pros': request.form.get('rec_0_pros', '').split('|'),
            'cons': request.form.get('rec_0_cons', '').split('|'),
            'resources': request.form.get('rec_0_resources', '').split('|')
        }

        if user_data['goal'] == "Higher Studies":
            inst = request.form.get('rec_0_institutions', '')
            rec['institutions'] = inst.split('|') if inst else []
        else:
            rec['companies'] = request.form.get('rec_0_companies', '').split('|')
            rec['salary_range'] = request.form.get('rec_0_salary', 'N/A')
            rec['growth'] = request.form.get('rec_0_growth', 'N/A')
            rec['skills_needed'] = request.form.get('rec_0_skills', '').split('|')

        html_content = f"""
        <html>
        <head>
            <style>
                @page {{ size: A4; margin: 1.5cm; }}
                body {{ font-family: 'Helvetica', 'Arial', sans-serif; color: #333; line-height: 1.6; font-size: 11pt; }}
                .header {{ border-bottom: 2px solid #4361ee; padding-bottom: 10px; margin-bottom: 30px; }}
                .header h1 {{ color: #4361ee; margin: 0; font-size: 24pt; }}
                .header p {{ color: #666; margin: 5px 0 0; }}
                .rec-title-box {{ background-color: #4361ee; color: white; padding: 20px; border-radius: 8px; margin-bottom: 25px; }}
                .rec-title-box h2 {{ margin: 0; font-size: 20pt; }}
                .section {{ margin-bottom: 25px; }}
                .section-title {{ color: #3f37c9; font-size: 14pt; font-weight: bold; border-left: 4px solid #4361ee; padding-left: 10px; margin-bottom: 10px; }}
                .box {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px; }}
                .pros-box {{ border-left: 4px solid #4cc9f0; }}
                .cons-box {{ border-left: 4px solid #f72585; }}
                ul {{ margin: 5px 0; padding-left: 20px; }}
                li {{ margin-bottom: 5px; }}
                .footer {{ text-align: center; color: #999; font-size: 9pt; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Detailed Career Analysis</h1>
                <p>Prepared for {user_data['name']} &bull; {user_data['goal']}</p>
            </div>

            <div class="rec-title-box">
                <h2>{rec['title']}</h2>
            </div>

            <div class="section">
                <div class="section-title">Overview</div>
                <p>{rec['overview']}</p>
            </div>

            <div class="section">
                <div class="section-title">In-Depth Analysis</div>
                <p>{rec['details']}</p>
            </div>

            <div class="section">
                <div class="section-title">The Balanced View</div>
                <div class="box pros-box">
                    <strong>Advantages:</strong>
                    <ul>{''.join([f'<li>{p}</li>' for p in rec['pros'] if p.strip()])}</ul>
                </div>
                <div class="box cons-box">
                    <strong>Challenges:</strong>
                    <ul>{''.join([f'<li>{c}</li>' for c in rec['cons'] if c.strip()])}</ul>
                </div>
            </div>
        """

        if user_data['goal'] == "Higher Studies":
            html_content += f"""
            <div class="section">
                <div class="section-title">Recommended Institutions</div>
                <ul>{''.join([f'<li>{i}</li>' for i in rec['institutions'] if i.strip()])}</ul>
            </div>
            """
        else:
            html_content += f"""
            <div class="section">
                <div class="section-title">Industry Insights</div>
                <p><strong>Target Companies:</strong> {', '.join(rec['companies'])}</p>
                <p><strong>Required Skills:</strong> {', '.join(rec.get('skills_needed', []))}</p>
                <p><strong>Market Outlook:</strong> {rec['growth']} ({rec['salary_range']})</p>
            </div>
            """

        html_content += f"""
            <div class="section">
                <div class="section-title">Learning Resources</div>
                <ul>{''.join([f'<li>{r}</li>' for r in rec['resources'] if r.strip()])}</ul>
            </div>

            <div class="footer">
                Generated by Career Compass AI &bull; {user_data['name']}'s Professional Roadmap
            </div>
        </body></html>
        """

        pdf_file = io.BytesIO()
        pisa.CreatePDF(html_content, dest=pdf_file)
        pdf_file.seek(0)
        return send_file(pdf_file, download_name=f"Detailed_Analysis_{rec['title'].replace(' ', '_')}.pdf", as_attachment=True, mimetype='application/pdf')
    except Exception as e:
        print("Download error:", e)
        return "An error occurred during PDF generation", 500

if __name__ == '__main__':
    # Use environment variables for host and port if needed, default to local dev
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    app.run(host='0.0.0.0', port=port, debug=debug)
