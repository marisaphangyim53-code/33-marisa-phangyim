import os
import re
import subprocess
import sys


def normalize_text(text):
    """ตัดสัญลักษณ์ ตัวพิมพ์เล็ก-ใหญ่ และเว้นวรรคส่วนเกิน"""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[!.,:="\'\(\)]', " ", text)
    return " ".join(text.split())


def extract_numbers(text):
    """ดึงตัวเลขทั้งหมดจากผลลัพธ์ของนักเรียน"""
    if not text:
        return []
    return [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", text)]


def run_student_code(filename, input_data):
    """สั่งรันโค้ดนักเรียน รองรับทั้งมีและไม่มี .py"""
    target_file = filename
    if not os.path.exists(target_file) and not target_file.endswith(".py"):
        target_file = filename + ".py"

    if not os.path.exists(target_file):
        return None, "File Not Found"

    try:
        process = subprocess.run(
            [sys.executable, target_file],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=5,
        )
        return process.stdout, process.stderr
    except subprocess.TimeoutExpired:
        return None, "Timeout (โปรแกรมวนลูปไม่จบ)"
    except Exception as e:
        return None, str(e)


# =========================================================
# เกณฑ์การตรวจยืดหยุ่นแยกรายข้อสำหรับ Set 10 (ข้อละ 4 คะแนน)
# =========================================================


def grade_exam_1(output, stderr, test_case):
    """ข้อ 1: แปลงนาทีเป็นชั่วโมงและนาที (Hours = mins // 60, Remainder = mins % 60)"""
    expected_h = test_case["hours"]
    expected_m = test_case["minutes"]
    nums = extract_numbers(output)

    if len(nums) >= 2 and nums[0] == expected_h and nums[1] == expected_m:
        return 1.0  # แสดงผลตัวเลขชั่วโมงและนาทีถูกต้องตามลำดับ
    elif expected_h in nums and expected_m in nums:
        return 1.0  # มีตัวเลขคำตอบทั้งสองครบถ้วน
    elif expected_h in nums or expected_m in nums:
        return 0.5  # คำนวณถูกต้องเฉพาะชั่วโมงหรือนาทีอย่างใดอย่างหนึ่ง
    elif len(nums) > 0:
        return 0.25  # แสดงผลตัวเลขใดๆ ออกมา
    return 0.0


def grade_exam_2(output, stderr, test_case):
    """ข้อ 2: เปรียบเทียบตัวเลข A และ B (A is greater / B is greater or equal)"""
    expected = test_case["expected"].lower()
    norm_out = normalize_text(output)

    if expected == "a is greater":
        if "a is greater" in norm_out or (
            "a" in norm_out and "greater" in norm_out and "b" not in norm_out
        ):
            return 1.0  # พิมพ์ A is greater ถูกต้อง
    elif expected == "b is greater or equal":
        if "b is greater" in norm_out or (
            "b" in norm_out and "greater" in norm_out
        ):
            return 1.0  # พิมพ์ B is greater or equal ถูกต้อง

    if "greater" in norm_out:
        return 0.5  # มีการใช้คำว่า greater ในการเปรียบเทียบ
    return 0.0


def grade_exam_3(output, stderr, test_case):
    """ข้อ 3: ตรวจสอบความยาวรหัสผ่าน (Pass / Too Short)"""
    expected = test_case["expected"].lower()
    norm_out = normalize_text(output)

    if expected in norm_out:
        return 1.0  # พิมพ์ Pass หรือ Too Short ถูกต้อง
    elif "pass" in norm_out or "short" in norm_out:
        return 0.5  # พิมพ์สถานะออกมาได้แต่เงื่อนไขสลับกัน
    return 0.0


def grade_exam_4(output, stderr, test_case):
    """ข้อ 4: สัญญาณไฟจราจร (Stop / Slow / Go / Invalid)"""
    expected = test_case["expected"].lower()
    norm_out = normalize_text(output)

    if expected in norm_out:
        return 1.0  # พิมพ์คำตอบตรงกับสัญญาณไฟถูกต้อง
    elif any(k in norm_out for k in ["stop", "slow", "go", "invalid"]):
        return 0.5  # พิมพ์คำสั่งสัญญาณไฟออกมาได้แต่เงื่อนไขสลับกัน
    return 0.0


def grade_exam_5(output, stderr, test_case):
    """ข้อ 5: คำนวณค่าไฟฟ้าตามหน่วยที่ใช้ (<=50 * 3 | <=100 * 4 | >100 * 5)"""
    expected = test_case["expected"]
    nums = extract_numbers(output)

    if any(abs(n - expected) < 0.1 for n in nums):
        return 1.0  # คำนวณค่าไฟตรงเงื่อนไข
    elif any(abs(n - (test_case["unit"] * rate)) < 0.1 for rate in [3, 4, 5]):
        return 0.5  # คำนวณค่าไฟถูกโครงสร้าง แต่ใช้ตัวคูณอัตราผิดช่วง
    elif len(nums) > 0:
        return 0.25  # แสดงผลตัวเลขใดๆ ออกมา
    return 0.0


# =========================================================
# ชุดข้อมูลทดสอบ (Test Cases สำหรับ Set 10)
# =========================================================
EXAMS = {
    "Examination_1.py": {
        "grader": grade_exam_1,
        "cases": [
            {"input": "130\n", "hours": 2, "minutes": 10},
            {"input": "60\n", "hours": 1, "minutes": 0},
            {"input": "45\n", "hours": 0, "minutes": 45},
            {"input": "185\n", "hours": 3, "minutes": 5},
        ],
    },
    "Examination_2.py": {
        "grader": grade_exam_2,
        "cases": [
            {"input": "10\n5\n", "expected": "A is greater"},
            {"input": "5\n10\n", "expected": "B is greater or equal"},
            {"input": "7\n7\n", "expected": "B is greater or equal"},
            {"input": "20\n15\n", "expected": "A is greater"},
        ],
    },
    "Examination_3.py": {
        "grader": grade_exam_3,
        "cases": [
            {"input": "12345678\n", "expected": "Pass"},
            {"input": "hello\n", "expected": "Too Short"},
            {"input": "password123\n", "expected": "Pass"},
            {"input": "abc\n", "expected": "Too Short"},
        ],
    },
    "Examination_4.py": {
        "grader": grade_exam_4,
        "cases": [
            {"input": "red\n", "expected": "Stop"},
            {"input": "yellow\n", "expected": "Slow"},
            {"input": "green\n", "expected": "Go"},
            {"input": "blue\n", "expected": "Invalid"},
        ],
    },
    "Examination_5.py": {
        "grader": grade_exam_5,
        "cases": [
            {"input": "30\n", "expected": 90, "unit": 30},
            {"input": "75\n", "expected": 300, "unit": 75},
            {"input": "100\n", "expected": 400, "unit": 100},
            {"input": "120\n", "expected": 600, "unit": 120},
        ],
    },
}

# =========================================================
# ประมวลผลและสร้าง Markdown สรุปคะแนน
# =========================================================
total_score = 0.0
summary_rows = []

for exam_name, exam_data in EXAMS.items():
    grader = exam_data["grader"]
    cases = exam_data["cases"]

    exam_score = 0.0
    passed_cases = 0.0

    for case in cases:
        stdout, stderr = run_student_code(exam_name, case["input"])
        if stdout is not None:
            score = grader(stdout, stderr, case)
            exam_score += score
            if score >= 1.0:
                passed_cases += 1.0
            elif score > 0:
                passed_cases += 0.5

    final_exam_score = min(4.0, round(exam_score, 1))
    total_score += final_exam_score

    if final_exam_score >= 4.0:
        status = "🟢 ผ่าน"
    elif final_exam_score > 0:
        status = "🟡 ผ่านบางส่วน"
    else:
        status = "❌ ไม่ผ่าน"

    score_display = (
        f"{int(final_exam_score)}"
        if final_exam_score.is_integer()
        else f"{final_exam_score}"
    )
    passed_display = (
        f"{int(passed_cases)}"
        if passed_cases.is_integer()
        else f"{passed_cases}"
    )

    summary_rows.append(
        f"| `{exam_name}` | {status} | {passed_display}/4 เคส | {score_display} / 4 |"
    )

final_total_display = (
    f"{int(total_score)}" if total_score.is_integer() else f"{total_score}"
)

markdown_summary = f"""
## 📊 สรุปผลการสอบวิชาเขียนโปรแกรม (Set 10)

| ข้อสอบ | สถานะการตรวจ | ผ่าน Test Cases | คะแนนที่ได้ |
| :--- | :--- | :--- | :--- |
""" + "\n".join(summary_rows) + f"""

### 🎯 คะแนนรวมทั้งหมด: {final_total_display} / 20 คะแนน
"""

print(markdown_summary)

github_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
if github_summary_path:
    with open(github_summary_path, "a", encoding="utf-8") as f:
        f.write(markdown_summary)
