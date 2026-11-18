import streamlit as st
import streamlit.components.v1 as components
import html
import io
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether
from reportlab.lib.units import mm
from openai import OpenAI

st.set_page_config(page_title="ResumeCraft AI", page_icon="📄", layout="wide")

# -------------------- TEMPLATE CATALOG --------------------
TEMPLATES = [
    {"name":"Classic Professional","category":"Professional","color":"#174A5B","layout":"classic","description":"A balanced, traditional business resume."},
    {"name":"Modern Professional","category":"Professional","color":"#6552C8","layout":"modern","description":"A contemporary layout with a clean sidebar."},
    {"name":"Business Teal","category":"Professional","color":"#087E78","layout":"sidebar","description":"A polished teal business design."},
    {"name":"Executive","category":"Professional","color":"#26364A","layout":"executive","description":"A refined layout for experienced professionals."},
    {"name":"Corporate Blue","category":"Professional","color":"#1769AA","layout":"sidebar","description":"A confident blue two-column design."},
    {"name":"Creative Modern","category":"Creative","color":"#8B70E8","layout":"sidebar","description":"A bold, contemporary creative resume."},
    {"name":"Creative Designer","category":"Creative","color":"#D45B76","layout":"creative","description":"A distinctive style for creative portfolios."},
    {"name":"Enhanced Professional","category":"Creative","color":"#009DB8","layout":"sidebar","description":"A bright, structured professional design."},
    {"name":"Elegant","category":"Creative","color":"#A27D58","layout":"elegant","description":"A subtle, elegant editorial look."},
    {"name":"Premium","category":"Creative","color":"#A17A25","layout":"executive","description":"A sophisticated dark-accent design."},
    {"name":"Minimalist","category":"Simple","color":"#333333","layout":"minimal","description":"A clean, single-column ATS-conscious layout."},
    {"name":"Student Fresher","category":"Simple","color":"#3C6E71","layout":"minimal","description":"A simple layout for students and graduates."},
    {"name":"Software Developer","category":"Simple","color":"#315A9B","layout":"minimal","description":"A skills and projects focused layout."},
    {"name":"Academic","category":"Simple","color":"#4C5968","layout":"academic","description":"A structured academic CV style."},
    {"name":"Clean Classic","category":"Simple","color":"#202020","layout":"minimal","description":"A straightforward, readable resume."},
]

st.markdown("""
<style>
.stApp {background:#F5F4F1;}
header[data-testid="stHeader"] {background:#F5F4F1;}
.block-container {padding-top:1rem; padding-bottom:2rem; max-width:100%;}
.brand {font-size:27px;font-weight:850;color:#2925C9;letter-spacing:-1px;}
.topnav {font-size:14px;color:#555;padding-top:9px;}
.section-title {font-size:25px;font-weight:750;color:#20212A;}
.muted {color:#777;font-size:14px;}
.step-card {background:#F0EFFA;border:1px solid #D8D5E8;border-radius:12px;padding:11px 12px;margin-bottom:7px;}
.step-active {background:#2420D4;color:white;border-radius:12px;padding:12px;margin-bottom:7px;}
.template-card {background:white;border:1px solid #D9D9D9;border-radius:13px;padding:9px;height:100%;}
div.stButton > button {border-radius:9px;font-weight:600;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius:12px;}
</style>
""", unsafe_allow_html=True)

# -------------------- SESSION DATA --------------------
DEFAULTS = {
    "target_role":"", "experience_level":"Student / Fresher",
    "name":"", "email":"", "phone":"", "location":"",
    "linkedin":"", "github":"", "portfolio":"",
    "summary":"", "experience":"", "education":"",
    "skills":"", "projects":"", "certifications":"",
    "languages":"", "additional":"", "template":"Modern Professional"
}
if "resume" not in st.session_state:
    st.session_state.resume = DEFAULTS.copy()
if "step" not in st.session_state:
    st.session_state.step = 6
if "ai_suggestion" not in st.session_state:
    st.session_state.ai_suggestion = ""

d = st.session_state.resume

def get_template(name):
    return next((x for x in TEMPLATES if x["name"] == name), TEMPLATES[0])

def safe(x):
    return html.escape(str(x or "")).replace("\n", "<br>")

def section_html(title, value):
    if not str(value or "").strip():
        return ""
    return f'<section><h3>{title}</h3><div class="bodycopy">{safe(value)}</div></section>'

def render_resume_html(data, template_name):
    t = get_template(template_name)
    c = t["color"]
    name = safe(data["name"] or "YOUR NAME")
    role = safe(data["target_role"] or "Professional Title")
    contact = " · ".join(x for x in [data["email"], data["phone"], data["location"]] if x.strip())
    links = " · ".join(x for x in [data["linkedin"], data["github"], data["portfolio"]] if x.strip())
    sidebar = t["layout"] in ("sidebar", "modern", "creative")
    profile = section_html("PROFILE", data["summary"])
    education = section_html("EDUCATION", data["education"])
    experience = section_html("EXPERIENCE", data["experience"])
    projects = section_html("PROJECTS", data["projects"])
    skills = section_html("SKILLS", data["skills"])
    certs = section_html("CERTIFICATIONS", data["certifications"])
    langs = section_html("LANGUAGES", data["languages"])
    extra = section_html("ADDITIONAL INFORMATION", data["additional"])
    if sidebar:
        left = f'<aside><h1>{name}</h1><b>{role}</b><p>{safe(contact)}</p><p>{safe(links)}</p>{skills}{education}{certs}{langs}</aside>'
        right = f'<main>{profile}{experience}{projects}{extra}</main>'
        content = left + right
    else:
        content = f'<header><h1>{name}</h1><h2>{role}</h2><p>{safe(contact)}</p><p>{safe(links)}</p></header><main>{profile}{education}{experience}{projects}{skills}{certs}{langs}{extra}</main>'
    return f"""
    <html><head><meta charset="utf-8"><style>
    *{{box-sizing:border-box}} body{{margin:0;background:#ececec;font-family:Arial,sans-serif;color:#242424;padding:12px}}
    .paper{{background:#fff;max-width:760px;min-height:930px;margin:auto;box-shadow:0 2px 14px #ccc;display:flex;overflow:hidden}}
    header{{padding:30px 34px 18px;border-bottom:3px solid {c};width:100%}}
    h1{{font-size:25px;margin:0 0 7px;color:{c};letter-spacing:.2px}}
    h2{{font-size:13px;margin:0 0 10px;color:#444;font-weight:600}}
    header p{{font-size:9px;line-height:1.6;margin:2px 0;color:#555}}
    aside{{background:{c};color:white;width:35%;padding:25px 18px;flex-shrink:0}}
    aside h1{{color:white;font-size:20px;line-height:1.2}}
    aside b{{font-size:11px}}
    aside p{{font-size:9px;line-height:1.6;overflow-wrap:anywhere}}
    aside h3{{color:white;border-bottom:1px solid #ffffff88}}
    main{{padding:25px 27px;flex:1;min-width:0}}
    section{{margin-bottom:17px;break-inside:avoid}}
    h3{{font-size:11px;letter-spacing:.7px;color:{c};border-bottom:1px solid #ddd;padding-bottom:5px;margin:0 0 8px}}
    .bodycopy{{font-size:9.5px;line-height:1.65;overflow-wrap:anywhere}}
    aside .bodycopy{{font-size:9px}}
    </style></head><body><div class="paper">{content}</div></body></html>
    """

def generate_pdf(data, template_name):
    t = get_template(template_name)
    accent = colors.HexColor(t["color"])
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=17*mm, leftMargin=17*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ResumeName", parent=styles["Title"], fontSize=22,
                                 leading=26, textColor=accent, alignment=0, spaceAfter=4)
    role_style = ParagraphStyle("Role", parent=styles["Normal"], fontSize=10,
                                textColor=colors.HexColor("#555555"), spaceAfter=6)
    head_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=11,
                                leading=14, textColor=accent, spaceBefore=11, spaceAfter=5)
    body_style = ParagraphStyle("ResumeBody", parent=styles["BodyText"], fontSize=8.8,
                                leading=12.5, spaceAfter=3, wordWrap="CJK")
    story = [Paragraph(escape(data["name"] or "Your Name"), title_style)]
    if data["target_role"]:
        story.append(Paragraph(escape(data["target_role"]), role_style))
    contact = " | ".join(x for x in [data["email"], data["phone"], data["location"],
                                     data["linkedin"], data["github"], data["portfolio"]] if x.strip())
    if contact:
        story.append(Paragraph(escape(contact), body_style))
    story += [Spacer(1, 8), HRFlowable(width="100%", thickness=1.4, color=accent)]
    sections = [
        ("PROFILE", data["summary"]), ("EDUCATION", data["education"]),
        ("EXPERIENCE", data["experience"]), ("PROJECTS", data["projects"]),
        ("SKILLS", data["skills"]), ("CERTIFICATIONS", data["certifications"]),
        ("LANGUAGES", data["languages"]), ("ADDITIONAL INFORMATION", data["additional"])
    ]
    for heading, value in sections:
        if value.strip():
            block = [Paragraph(escape(heading), head_style)]
            for line in value.splitlines():
                if line.strip():
                    block.append(Paragraph(escape(line), body_style))
            story.append(KeepTogether(block))
    doc.build(story)
    output.seek(0)
    return output.getvalue()

def ai_call(prompt):
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        key = ""
    if not key:
        return None, "AI is not configured. Add GROQ_API_KEY in Streamlit Secrets. Manual resume building still works."
    try:
        client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
        result = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role":"system","content":"You are a careful resume writing assistant. Improve wording without inventing facts, qualifications, metrics or achievements. Use concise professional language."},
                {"role":"user","content":prompt}
            ],
            max_tokens=1000
        )
        return result.choices[0].message.content, None
    except Exception as e:
        return None, f"AI request failed: {e}"

# -------------------- TOP NAV --------------------
top = st.columns([1.1, 5, .45])
with top[0]:
    st.markdown('<div class="brand">resumecraft</div>', unsafe_allow_html=True)
with top[1]:
    st.markdown('<div class="topnav">Home　　Resume Builder　　AI Assistant　　Career Tips</div>', unsafe_allow_html=True)
with top[2]:
    st.markdown("**RC**")
st.divider()

# -------------------- THREE PANEL LAYOUT --------------------
left, center, right = st.columns([0.82, 2.45, 1.55], gap="medium")

steps = ["Job Target", "Basic Info", "Experience", "Education", "Skills", "Additional", "Template"]
with left:
    st.markdown("### Resume Builder")
    for i, label in enumerate(steps):
        if st.button(("✓  " if i < st.session_state.step else (f"{i+1}  ")) + label,
                     key=f"step_{i}", use_container_width=True,
                     type="primary" if i == st.session_state.step else "secondary"):
            st.session_state.step = i
            st.rerun()
    st.caption(f"Step {st.session_state.step + 1} of 7")

with center:
    step = st.session_state.step
    st.markdown(f'<div class="section-title">{steps[step] if step < 6 else "Choose a Template"}</div>', unsafe_allow_html=True)
    descriptions = [
        "Tell us what kind of opportunity you are targeting.",
        "Add your contact information and professional summary.",
        "Add your employment and internship experience. Freshers can skip this step.",
        "Add your educational qualifications.",
        "Add relevant technical and soft skills.",
        "Add certifications, languages and other useful details.",
        "Select a professional template for your resume."
    ]
    st.markdown(f'<p class="muted">{descriptions[step]}</p>', unsafe_allow_html=True)

    if step == 0:
        with st.form("job_form"):
            d["target_role"] = st.text_input("Target job title / role", value=d["target_role"], placeholder="e.g. Python Developer")
            d["experience_level"] = st.selectbox("Your current level",
                ["Student / Fresher", "Entry-level", "Experienced Professional", "Career Changer"],
                index=["Student / Fresher","Entry-level","Experienced Professional","Career Changer"].index(d["experience_level"]))
            if st.form_submit_button("Save and continue", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
    elif step == 1:
        with st.form("basic_form"):
            d["name"] = st.text_input("Full name", value=d["name"])
            c1,c2 = st.columns(2)
            d["email"] = c1.text_input("Email", value=d["email"])
            d["phone"] = c2.text_input("Phone", value=d["phone"])
            d["location"] = st.text_input("City / Location", value=d["location"])
            d["linkedin"] = st.text_input("LinkedIn URL", value=d["linkedin"])
            d["github"] = st.text_input("GitHub URL", value=d["github"])
            d["portfolio"] = st.text_input("Portfolio URL", value=d["portfolio"])
            d["summary"] = st.text_area("Professional summary / career objective", value=d["summary"], height=130)
            if st.form_submit_button("Save and continue", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
    elif step == 2:
        with st.form("experience_form"):
            d["experience"] = st.text_area("Experience and internships", value=d["experience"], height=260,
                placeholder="Job title | Company | Dates\nDescribe your responsibilities and achievements. Add each role separately.")
            if st.form_submit_button("Save and continue", use_container_width=True):
                st.session_state.step = 3
                st.rerun()
        st.caption("No work experience yet? Leave this blank and continue.")
    elif step == 3:
        with st.form("education_form"):
            d["education"] = st.text_area("Education details", value=d["education"], height=230,
                placeholder="Degree | College | Graduation year | CGPA / Percentage\nAdd each qualification on a separate line.")
            if st.form_submit_button("Save and continue", use_container_width=True):
                st.session_state.step = 4
                st.rerun()
    elif step == 4:
        with st.form("skills_form"):
            d["skills"] = st.text_area("Skills", value=d["skills"], height=160,
                placeholder="Python, SQL, Machine Learning, Communication...")
            if st.form_submit_button("Save and continue", use_container_width=True):
                st.session_state.step = 5
                st.rerun()
    elif step == 5:
        with st.form("additional_form"):
            d["projects"] = st.text_area("Projects", value=d["projects"], height=130)
            d["certifications"] = st.text_area("Certifications", value=d["certifications"], height=90)
            d["languages"] = st.text_input("Languages", value=d["languages"])
            d["additional"] = st.text_area("Additional information (optional)", value=d["additional"], height=80)
            if st.form_submit_button("Save and choose template", use_container_width=True):
                st.session_state.step = 6
                st.rerun()
    else:
        search = st.text_input("⌕  Search templates...", placeholder="Search templates...")
        cat = st.radio("Categories", ["All Categories","Professional","Creative","Simple"],
                       horizontal=True, label_visibility="collapsed")
        view = st.radio("View", ["Grid View","List View"], horizontal=True, label_visibility="collapsed")
        filtered = [t for t in TEMPLATES if (cat == "All Categories" or t["category"] == cat)
                    and search.lower() in (t["name"] + t["description"] + t["category"]).lower()]
        if not filtered:
            st.info("No templates match your search.")
        if view == "Grid View":
            cols = st.columns(3)
            for i,t in enumerate(filtered):
                with cols[i % 3]:
                    selected = d["template"] == t["name"]
                    st.markdown(f"""
                    <div class="template-card">
                      <div style="height:145px;border:1px solid #ddd;border-radius:8px;display:flex;overflow:hidden;background:white">
                        <div style="width:31%;background:{t['color']};padding:10px 6px;color:white;font-size:8px">
                          <b>YOUR NAME</b><hr style="border-color:#ffffff88">
                          PROFILE<br><br>SKILLS<br><br>EDUCATION
                        </div>
                        <div style="padding:12px 9px;flex:1;color:#333;font-size:8px">
                          <b style="color:{t['color']}">PROFILE</b><hr>
                          Professional summary and career highlights.<br><br>
                          <b style="color:{t['color']}">EXPERIENCE</b><hr>
                          Work history and project details.
                        </div>
                      </div>
                      <div style="padding:8px 1px 2px"><b>{html.escape(t['name'])}</b><br>
                      <span style="font-size:11px;color:#777">{html.escape(t['description'])}</span></div>
                    </div>""", unsafe_allow_html=True)
                    if st.button("✓ Selected" if selected else "Select Template",
                                 key="choose_"+t["name"], use_container_width=True,
                                 type="primary" if selected else "secondary"):
                        d["template"] = t["name"]
                        st.rerun()
        else:
            for t in filtered:
                c1,c2 = st.columns([4,1])
                c1.markdown(f"**{t['name']}** · {t['category']}  \n{t['description']}")
                if c2.button("Selected" if d["template"] == t["name"] else "Select",
                             key="list_"+t["name"], use_container_width=True):
                    d["template"] = t["name"]
                    st.rerun()
        st.success(f"Selected template: {d['template']}")
        st.caption("Your information is retained when you switch templates.")

    # Navigation controls for all steps
    if step < 6:
        nav1, nav2 = st.columns(2)
        with nav1:
            if step > 0 and st.button("← Previous", use_container_width=True):
                st.session_state.step -= 1
                st.rerun()
        with nav2:
            if st.button("Next step →", use_container_width=True):
                st.session_state.step = min(6, step + 1)
                st.rerun()

with right:
    st.markdown("### Preview")
    st.caption("Live preview · updates after saving a step")
    st.markdown(f"**{d['template']}**")
    components.html(render_resume_html(d, d["template"]), height=770, scrolling=True)
    st.divider()
    if st.button("Download PDF", use_container_width=True, type="primary"):
        if not d["name"].strip():
            st.warning("Enter your name in Basic Info before downloading.")
        else:
            try:
                pdf_bytes = generate_pdf(d, d["template"])
                st.download_button("⬇ Download resume PDF", data=pdf_bytes,
                    file_name="ResumeCraft_Resume.pdf", mime="application/pdf",
                    use_container_width=True)
            except Exception as e:
                st.error(f"Could not generate PDF: {e}")

# -------------------- AI ASSISTANT --------------------
st.divider()
with st.expander("✨ AI Resume Assistant", expanded=False):
    st.write("Improve your wording while keeping your real experience and achievements accurate.")
    task = st.selectbox("What would you like help with?",
        ["Improve my professional summary","Improve project description",
         "Improve experience bullet points","Suggest skills for my target role"])
    source_map = {
        "Improve my professional summary": d["summary"],
        "Improve project description": d["projects"],
        "Improve experience bullet points": d["experience"],
        "Suggest skills for my target role": d["target_role"]
    }
    source = st.text_area("Text or job role", value=source_map[task], key="ai_source")
    if st.button("Generate AI suggestion"):
        if not source.strip():
            st.warning("Enter some text first.")
        else:
            prompt = f"Task: {task}\nTarget role: {d['target_role']}\nUser content: {source}\nReturn a concise, useful result."
            with st.spinner("Generating suggestion..."):
                answer, error = ai_call(prompt)
            if error:
                st.error(error)
            else:
                st.session_state.ai_suggestion = answer
    if st.session_state.ai_suggestion:
        st.text_area("AI suggestion — review before using", value=st.session_state.ai_suggestion, height=160)
        st.caption("Copy the approved suggestion into the relevant resume section.")

st.caption("ResumeCraft AI · Build a clear, professional resume. Your entries remain in this browser session; download a copy before closing.")
