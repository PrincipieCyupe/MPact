"""
Extract structured fields from resume text.
Conservative: better to leave a field empty than fill it with garbage.
"""
import re

SECTION_HEADERS = {
    'experience', 'work experience', 'employment', 'employment history', 'career history',
    'professional experience', 'work history', 'internship', 'internships',
    'education', 'academic background', 'qualifications', 'academic qualifications',
    'skills', 'technical skills', 'core competencies', 'competencies', 'expertise',
    'technologies', 'tech stack', 'tools', 'languages', 'programming languages',
    'projects', 'personal projects', 'portfolio', 'open source', 'key projects',
    'summary', 'profile', 'professional summary', 'objective', 'about', 'about me',
    'certifications', 'certificates', 'achievements', 'awards', 'publications',
    'references', 'contact', 'interests', 'hobbies', 'volunteering', 'activities',
    'leadership', 'honors', 'courses', 'coursework', 'training',
}

# Headers that signal work experience — used to stop project parsing
EXPERIENCE_HEADERS = {
    'experience', 'work experience', 'employment', 'employment history', 'career history',
    'professional experience', 'work history', 'internship', 'internships',
}

EDUCATION_LEVELS = [
    ('phd',       ['ph.d', 'phd', 'doctorate', 'doctor of philosophy', 'dphil']),
    ('masters',   ['master of', 'msc', 'mba', 'm.s.', 'm.a.', 'm.eng', 'postgrad', 'pgd']),
    ('bachelors', ['bachelor', 'bsc', 'b.s.', 'b.a.', 'b.eng', 'b.tech', 'undergrad']),
    ('diploma',   ['diploma', 'hnd', 'associate degree', 'certificate']),
    ('highschool', ['high school', 'secondary school', 'a-level', 'gcse']),
]

KNOWN_CITIES = re.compile(
    r'\b(Kigali|Nairobi|Kampala|Lagos|Accra|Dakar|Abuja|Lomé|Cotonou|'
    r'Addis\s+Ababa|Dar\s+es\s+Salaam|Lusaka|Harare|Douala|Yaoundé|Casablanca|Cairo|'
    r'Johannesburg|Cape\s+Town|Durban|Pretoria|Maputo|Antananarivo|'
    r'London|Paris|Berlin|Amsterdam|Barcelona|Madrid|Rome|'
    r'New\s+York|San\s+Francisco|Seattle|Austin|Chicago|Toronto|Vancouver|'
    r'Dubai|Singapore|Kuala\s+Lumpur|Remote)\b',
    re.IGNORECASE
)

KNOWN_COUNTRIES = re.compile(
    r'\b(Rwanda|Kenya|Uganda|Nigeria|Ghana|Senegal|Ethiopia|Tanzania|Zambia|Zimbabwe|'
    r'Cameroon|Côte\s+d.Ivoire|Ivory\s+Coast|Morocco|Egypt|South\s+Africa|'
    r'USA|United\s+States|UK|United\s+Kingdom|Canada|Australia|'
    r'Netherlands|France|Germany|Spain|Italy|Remote)\b',
    re.IGNORECASE
)

SENTENCE_WORDS = re.compile(
    r'\b(and|the|of|in|for|to|a|an|with|using|through|while|by|is|are|was|were|'
    r'have|has|had|be|been|being|from|at|on|as|or|but|not|this|that|which|who|'
    r'when|where|how|what|developing|working|managing|leading|building|creating|'
    r'designing|implementing|responsible|ensuring|maintaining|providing|support)\b',
    re.IGNORECASE
)

# Patterns that disqualify a token from being a skill
SKILL_REJECTS = re.compile(
    r'\b(officer|manager|director|engineer at|developer at|lead|specialist|analyst|'
    r'coordinator|administrator|assistant|intern|associate|executive|supervisor|head of|'
    r'foundation|institute|university|college|school|ltd|limited|inc\b|corp\b|company|'
    r'organization|association|agency|ministry|department|bureau|centre|center|'
    r'present|current|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|'
    r'january|february|march|april|june|july|august|september|october|november|december)\b',
    re.IGNORECASE
)

# Date/range patterns — disqualify a line as a skill chunk
DATE_PATTERN = re.compile(
    r'\b(19|20)\d{2}\b'         # Year like 2024
    r'|\b\d{4}\s*[-–—]\s*(\d{4}|present|current)\b'  # 2022 - 2024 or 2022 - Present
    r'|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b',
    re.IGNORECASE
)

# Lines that look like "Job Title | Company | Location | Date"
EXPERIENCE_LINE = re.compile(
    r'\|'                           # pipe separator common in experience lines
    r'|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}'
    r'|\d{4}\s*[-–—]\s*(?:\d{4}|present|current)',
    re.IGNORECASE
)

# Bullet/list prefixes to strip
BULLET_PREFIX = re.compile(r'^[\s•·\-–—►▸▶→✓✔○●◆◇▪▫]+')


def _is_sentence(text: str) -> bool:
    words = text.split()
    if len(words) < 3:
        return False
    matches = len(SENTENCE_WORDS.findall(text))
    return matches >= 2 or (matches >= 1 and len(words) > 5)


def _clean_header(line: str) -> str:
    """Normalise a line for header matching."""
    return re.sub(r'[^a-z\s]', '', line.lower()).strip()


def _find_section(lines: list, header_names: set) -> int:
    """Return index of line AFTER first matching section header, or -1."""
    for i, line in enumerate(lines):
        raw = line.lower().strip().rstrip(':')
        if raw in header_names or raw.rstrip('s') in header_names:
            return i + 1
        cleaned = _clean_header(line)
        if cleaned in header_names or cleaned.rstrip('s') in header_names:
            return i + 1
    return -1


def _next_section_index(lines: list, start: int) -> int:
    """Return index of the next section header after start, or len(lines)."""
    for i, line in enumerate(lines[start:], start):
        raw = line.lower().strip().rstrip(':')
        cleaned = _clean_header(line)
        if (raw in SECTION_HEADERS or raw.rstrip('s') in SECTION_HEADERS
                or cleaned in SECTION_HEADERS or cleaned.rstrip('s') in SECTION_HEADERS):
            return i
    return len(lines)


def _is_experience_line(line: str) -> bool:
    """True if the line looks like a work-experience entry rather than a project description."""
    if EXPERIENCE_LINE.search(line):
        return True
    if DATE_PATTERN.search(line):
        return True
    # Lines with just a role+company pattern like "IT Officer, Org Name"
    if SKILL_REJECTS.search(line) and (',' in line or '|' in line):
        return True
    return False


def parse_resume_fields(text: str) -> dict:
    """Return extracted fields dict. Only fills fields we are confident about."""
    result = {}
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    low = text.lower()

    # ── Email ──
    m = re.search(r'[\w.+\-]+@[\w\-]+\.\w{2,}', text)
    if m:
        result['email'] = m.group(0).lower()

    # ── Phone ──
    for pat in [
        r'\+\d{1,3}[\s\-]?\d{2,4}[\s\-]?\d{3}[\s\-]?\d{3,4}',
        r'\+\d{10,14}',
        r'0\d{9,11}',
    ]:
        m = re.search(pat, text)
        if m:
            raw = m.group(0).strip()
            digits = re.sub(r'\D', '', raw)
            if 8 <= len(digits) <= 15:
                result['phone'] = raw
                break

    # ── Name ── first short capitalised line near top
    for line in lines[:8]:
        if '@' in line or 'http' in line.lower():
            continue
        if len(line) > 55 or len(line) < 4:
            continue
        if re.search(r'\d{2,}', line):
            continue
        raw_lower = line.lower().rstrip(':')
        if raw_lower in SECTION_HEADERS or _clean_header(line) in SECTION_HEADERS:
            continue
        if any(kw in line.lower() for kw in ('linkedin', 'github', 'portfolio', 'resume', 'curriculum')):
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(re.match(r"^[A-Za-zÀ-ÿ'\-\.]+$", w) for w in words):
            if sum(1 for w in words if w[0].isupper()) >= len(words) - 1:
                result['name'] = line
                break

    # ── Location ── explicit label first
    for line in lines:
        m = re.match(r'^(?:location|city|address|based\s+in|residing\s+in)\s*[:\-]\s*(.{3,80})$', line, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if not _is_sentence(val) and len(val.split()) <= 6:
                result['location'] = val[:100]
                break
    if 'location' not in result:
        for line in lines:
            if len(line.split()) > 6 or len(line) > 60:
                continue
            if _is_sentence(line):
                continue
            if KNOWN_CITIES.search(line) or KNOWN_COUNTRIES.search(line):
                if not any(kw in line.lower() for kw in ('university', 'college', 'institute', 'school', 'ltd', 'inc', 'corp')):
                    result['location'] = line.strip()[:100]
                    break

    # ── Years of experience ──
    for pat in [
        r'(\d+)\+?\s+years?\s+(?:of\s+)?(?:professional\s+)?(?:software\s+|relevant\s+)?(?:experience|exp\.?)',
        r'(?:over|more\s+than|approximately|around)\s+(\d+)\s+years?',
        r'(\d+)\+?\s+years?\s+(?:in\s+the\s+)?(?:industry|field|sector)',
    ]:
        m = re.search(pat, low)
        if m:
            y = int(m.group(1))
            if 0 < y <= 40:
                result['years_experience'] = y
                break

    # ── Education level ──
    for level, keywords in EDUCATION_LEVELS:
        if any(kw in low for kw in keywords):
            result['education_level'] = level
            break

    # ── Education details ── line starting with a degree abbreviation
    degree_pat = re.compile(
        r'^(Bachelor|B\.?Sc?\.?|B\.?A\.?|B\.?Tech|B\.?Eng|'
        r'Master|M\.?Sc?\.?|M\.?A\.?|M\.?B\.?A|M\.?Eng|'
        r'Ph\.?D|Doctorate|Diploma|Certificate|Associate)\b',
        re.IGNORECASE
    )
    for line in lines:
        if degree_pat.match(line) and 8 < len(line) < 160:
            result['education'] = re.sub(r'\s+', ' ', line.strip())[:200]
            break

    # ── Skills ──
    # Only extract from a dedicated skills section header
    skill_header_names = {
        'skills', 'skill', 'technical skills', 'core competencies', 'competencies',
        'expertise', 'technologies', 'tech stack', 'tools', 'programming languages',
        'languages', 'tools & technologies', 'tools and technologies',
        'technical expertise', 'key skills', 'areas of expertise',
    }
    si = _find_section(lines, skill_header_names)
    if si >= 0:
        section_end = _next_section_index(lines, si)
        raw_skills = []
        for line in lines[si:min(si + 15, section_end)]:
            # Skip lines that look like experience entries
            if _is_experience_line(line):
                continue
            # Skip sentence-like lines
            if _is_sentence(line):
                continue
            # Split on common skill separators
            for chunk in re.split(r'[,|•·\t/]+', line):
                chunk = BULLET_PREFIX.sub('', chunk).strip().rstrip('•·*-–—►▸▶→')
                if not chunk:
                    continue
                # Reject if it contains year/date or role/org keywords
                if DATE_PATTERN.search(chunk):
                    continue
                if SKILL_REJECTS.search(chunk):
                    continue
                # Reject if it contains a known city/country (it's likely a location)
                if KNOWN_CITIES.search(chunk) or KNOWN_COUNTRIES.search(chunk):
                    continue
                # Valid: 2-40 chars, starts with letter or digit, not a sentence
                if (2 <= len(chunk) <= 40
                        and re.match(r'^[A-Za-z0-9]', chunk)
                        and not _is_sentence(chunk)
                        and chunk.lower().rstrip(':') not in SECTION_HEADERS):
                    raw_skills.append(chunk)
        if raw_skills:
            result['skills'] = ', '.join(raw_skills[:20])

    # ── Projects ──
    # Only pull from a dedicated Projects section — never bleed into Experience
    proj_header_names = {
        'projects', 'project', 'personal projects', 'portfolio',
        'selected projects', 'key projects', 'open source',
        'side projects', 'academic projects', 'notable projects',
    }
    pi = _find_section(lines, proj_header_names)
    if pi >= 0:
        section_end = _next_section_index(lines, pi)
        proj_lines = []
        for line in lines[pi:min(pi + 20, section_end)]:
            # Hard skip: if the line looks like a work-experience date range entry
            if _is_experience_line(line) and len(proj_lines) == 0:
                # If first lines are experience-style, we likely found the wrong section
                break
            proj_lines.append(line)
        if proj_lines:
            result['projects'] = '\n'.join(proj_lines)[:1000]

    return result
