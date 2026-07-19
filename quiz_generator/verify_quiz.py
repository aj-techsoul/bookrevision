import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from quiz_generator.quiz_generator import QuizGenerator
except ModuleNotFoundError:
    from quiz_generator import QuizGenerator

def test_quiz_generator():
    print("Initializing QuizGenerator...")
    qg = QuizGenerator()
    
    print("\n--- TEST 1: Short notes check ---")
    short_text = "The water cycle is continuous movement of water."
    try:
        qg.generate_quiz(short_text, num_questions=1)
        print("❌ FAILED: Short text was not rejected!")
    except ValueError as e:
        print("✅ SUCCESS: Correctly rejected short text with error:")
        print(f"   '{e}'")
        
    print("\n--- TEST 2: High-quality MCQ generation ---")
    normal_text = (
        "The water cycle, also known as the hydrological cycle, describes the continuous movement "
        "of water on, above, and below Earth's surface. "
        "Water evaporates from the surface, rises into the atmosphere, cools, and condenses into clouds. "
        "Precipitation falls back to Earth as rain or snow, and collects in rivers, lakes, and oceans. "
        "Plants absorb water through their roots and release it through transpiration into the atmosphere. "
        "Evaporation is the transition of liquid water to a gas phase, driven primarily by solar radiation. "
        "Condensation occurs when water vapor in the air cools and changes back into liquid water droplets, forming clouds. "
        "Precipitation is the process where condensed water droplets grow large enough to fall under gravity."
    )
    
    try:
        questions = qg.generate_quiz(normal_text, num_questions=3, difficulty='medium')
        print(f"✅ SUCCESS: Generated {len(questions)} questions.")
        
        for i, q in enumerate(questions, 1):
            print(f"\nQ{i}: {q['question']}")
            for letter, option in q['options'].items():
                print(f"  {letter}: {option}")
            print(f"  Correct Answer: {q['correct']}")
            print(f"  Difficulty: {q['difficulty']}")
            
            # Verify options uniqueness
            options_set = set(q['options'].values())
            assert len(options_set) == 4, "❌ Duplicate options found!"
            
            # Verify no word-matching questions
            question_lower = q['question'].lower()
            forbidden = ["which word appears", "which sentence is present", "what is the third word"]
            for f in forbidden:
                assert f not in question_lower, f"❌ Forbidden word-matching pattern '{f}' found in question!"
                
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"❌ TEST FAILED with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quiz_generator()
