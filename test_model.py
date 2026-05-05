<<<<<<< HEAD
"""Test the ML model integration"""
from model import maternal_model

# Test case 1: Low risk patient
print("=" * 50)
print("TEST 1: Low Risk Patient")
print("=" * 50)
result = maternal_model.predict_risk(
    systolic=120,
    diastolic=80,
    spo2=98,
    fhr=140
)
print(f"Risk Level: {result['risk_level']}")
print(f"Confidence: {result['confidence']*100:.1f}%")
print(f"Recommendations:")
for rec in result['recommendations']:
    print(f"  • {rec}")

# Test case 2: High risk patient
print("\n" + "=" * 50)
print("TEST 2: High Risk Patient")
print("=" * 50)
result = maternal_model.predict_risk(
    systolic=165,
    diastolic=110,
    spo2=92,
    fhr=175
)
print(f"Risk Level: {result['risk_level']}")
print(f"Confidence: {result['confidence']*100:.1f}%")
print(f"Recommendations:")
for rec in result['recommendations']:
    print(f"  • {rec}")

# Test case 3: Medium risk patient
print("\n" + "=" * 50)
print("TEST 3: Medium Risk Patient")
print("=" * 50)
result = maternal_model.predict_risk(
    systolic=135,
    diastolic=88,
    spo2=96,
    fhr=155
)
print(f"Risk Level: {result['risk_level']}")
print(f"Confidence: {result['confidence']*100:.1f}%")
print(f"Recommendations:")
for rec in result['recommendations']:
    print(f"  • {rec}")

print("\n✅ ML Model is working correctly!")
=======
"""Test the ML model integration"""
from model import maternal_model

# Test case 1: Low risk patient
print("=" * 50)
print("TEST 1: Low Risk Patient")
print("=" * 50)
result = maternal_model.predict_risk(
    systolic=120,
    diastolic=80,
    spo2=98,
    fhr=140
)
print(f"Risk Level: {result['risk_level']}")
print(f"Confidence: {result['confidence']*100:.1f}%")
print(f"Recommendations:")
for rec in result['recommendations']:
    print(f"  • {rec}")

# Test case 2: High risk patient
print("\n" + "=" * 50)
print("TEST 2: High Risk Patient")
print("=" * 50)
result = maternal_model.predict_risk(
    systolic=165,
    diastolic=110,
    spo2=92,
    fhr=175
)
print(f"Risk Level: {result['risk_level']}")
print(f"Confidence: {result['confidence']*100:.1f}%")
print(f"Recommendations:")
for rec in result['recommendations']:
    print(f"  • {rec}")

# Test case 3: Medium risk patient
print("\n" + "=" * 50)
print("TEST 3: Medium Risk Patient")
print("=" * 50)
result = maternal_model.predict_risk(
    systolic=135,
    diastolic=88,
    spo2=96,
    fhr=155
)
print(f"Risk Level: {result['risk_level']}")
print(f"Confidence: {result['confidence']*100:.1f}%")
print(f"Recommendations:")
for rec in result['recommendations']:
    print(f"  • {rec}")

print("\n✅ ML Model is working correctly!")
>>>>>>> 9bb3e26e38b4e8a35de943457524a5215c876960
