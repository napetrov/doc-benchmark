import json
import os

inbound_dir = "../media/inbound"
files = [
    "file_1564---c23adc35-4806-44af-ae3a-96709e741dae.md",
    "file_1565---dbb78bb8-7d80-4152-808e-770fce8ddc42.md",
    "file_1566---13a0ce56-be97-460d-a297-5e09dd53ca2f.md"
]

static_must_haves = {
    "oneTBB": ["Q013", "Q001"],
    "oneMKL": ["Q022", "Q003", "Q005", "Q018", "Q023"],
    "oneDAL": ["Q005", "Q010", "Q021", "Q020"]
}

for fname in files:
    fpath = os.path.join(inbound_dir, fname)
    if not os.path.exists(fpath):
        continue
    
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            data = json.loads(content[start:end])
        else:
            continue
            
    library = data.get("library")
    library_lower = library.lower()
    
    must_haves = static_must_haves.get(library, [])
    
    transformed_questions = []
    for q in data.get("questions", []):
        # Transform to match benchmark.py Question dataclass
        tq = {
            "id": f"{library_lower}-{q['id']}",  # Make ID unique globally
            "text": q["question"],
            "category": q.get("category", "general"),
            "difficulty": str(q.get("difficulty", "intermediate")),
            "expected_topics": q.get("expected_answer_points", []),
            "metadata": {
                "persona": q.get("persona", ""),
                "must_cite": q.get("must_cite", []),
                "why_it_matters": q.get("why_it_matters", ""),
                "is_static_golden": q["id"] in must_haves,
                "original_id": q["id"]
            }
        }
        transformed_questions.append(tq)
        
    output_data = {
        "library": library,
        "library_id": f"intel/{library_lower}",
        "description": f"Golden regression set for {library}",
        "version_or_doc_snapshot": data.get("version_or_doc_snapshot", ""),
        "questions": transformed_questions
    }
    
    output_path = f"questions/{library_lower}_golden.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"Saved {library} -> {output_path} with {len(transformed_questions)} questions.")
