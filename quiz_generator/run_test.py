from quiz_generator import QuizGenerator

sample_text = (
    "The water cycle, also known as the hydrological cycle, describes the continuous movement "
    "of water on, above, and below Earth's surface. "
    "Water evaporates from the surface, rises into the atmosphere, cools, and condenses into clouds. "
    "Precipitation falls back to Earth as rain or snow, and collects in rivers, lakes, and oceans. "
    "Plants absorb water through their roots and release it through transpiration into the atmosphere."
)

print("Loading model...")
qg = QuizGenerator()
print("Generating quiz...")
questions = qg.generate_quiz(sample_text, num_questions=3)

for i, q in enumerate(questions, 1):
    print(f"\nQ{i}: {q['question']}")
    for k, v in q['options'].items():
        print(f"  {k}: {v}")
    print(f"  Correct: {q['correct']}")
    print(f"  Difficulty: {q.get('difficulty', 'N/A')}")
    if q.get('fallback'):
        print("  (fallback question)")
