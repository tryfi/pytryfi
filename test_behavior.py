#!/usr/bin/env python3
"""Test behavior functionality in standalone pytryfi"""

from pytryfi.fiPet import FiPet
from pytryfi.common import query
import datetime

# Test FiPet instantiation
pet = FiPet('test-pet-123')
print("✓ FiPet created successfully")

# Test that all behavior properties exist and default to 0
behavior_properties = [
    'dailyBarkingCount', 'dailyBarkingDuration',
    'weeklyBarkingCount', 'weeklyBarkingDuration', 
    'monthlyBarkingCount', 'monthlyBarkingDuration',
    'dailyLickingCount', 'dailyLickingDuration',
    'weeklyLickingCount', 'weeklyLickingDuration',
    'monthlyLickingCount', 'monthlyLickingDuration',
    'dailyScratchingCount', 'dailyScratchingDuration',
    'weeklyScratchingCount', 'weeklyScratchingDuration',
    'monthlyScratchingCount', 'monthlyScratchingDuration',
    'dailyEatingCount', 'dailyEatingDuration',
    'weeklyEatingCount', 'weeklyEatingDuration',
    'monthlyEatingCount', 'monthlyEatingDuration',
    'dailyDrinkingCount', 'dailyDrinkingDuration',
    'weeklyDrinkingCount', 'weeklyDrinkingDuration',
    'monthlyDrinkingCount', 'monthlyDrinkingDuration',
    'behaviorTimeline'
]

print("\nChecking behavior properties:")
for prop in behavior_properties:
    if hasattr(pet, prop):
        value = getattr(pet, prop)
        if prop == 'behaviorTimeline':
            expected = []
            passed = value == expected
        else:
            expected = 0
            passed = value == expected
        status = "✓" if passed else "✗"
        print(f"  {status} {prop}: {value} (expected: {expected})")
    else:
        print(f"  ✗ {prop}: MISSING")

# Test setBehaviorStatsFromTrends with sample data
print("\nTesting setBehaviorStatsFromTrends with sample data:")
sample_trends = [
    {
        'id': 'cleaning_self:DAY',
        'title': 'Licking',
        'summaryComponents': {
            'eventsSummary': '2 events',
            'durationSummary': '5m'
        },
        'chart': {
            '__typename': 'PetHealthTrendSegmentedTimeline',
            'segments': [
                {'color': '#ffffff', 'offset': 0, 'length': 86000},
                {'color': '#ff0000', 'offset': 36000, 'length': 180},  # 10am for 3 min
                {'color': '#ff0000', 'offset': 54000, 'length': 120},  # 3pm for 2 min
            ]
        }
    },
    {
        'id': 'scratching:DAY', 
        'title': 'Scratching',
        'summaryComponents': {
            'eventsSummary': '1 event',
            'durationSummary': '<1m'
        }
    }
]

pet.setBehaviorStatsFromTrends(sample_trends)

# Check if values were set correctly
print(f"  Licking count: {pet.dailyLickingCount} (expected: 2)")
print(f"  Licking duration: {pet.dailyLickingDuration} (expected: 300)")
print(f"  Scratching count: {pet.dailyScratchingCount} (expected: 1)")
print(f"  Scratching duration: {pet.dailyScratchingDuration} (expected: 30)")
print(f"  Timeline events: {len(pet.behaviorTimeline)} events")

# Test with None/empty eventsSummary (the bug we fixed)
print("\nTesting with None eventsSummary (bug fix test):")
try:
    trends_with_none = [
        {
            'id': 'cleaning_self:DAY',
            'summaryComponents': {
                'eventsSummary': None,  # This was causing the NoneType error
                'durationSummary': None
            }
        }
    ]
    pet.setBehaviorStatsFromTrends(trends_with_none)
    print("  ✓ Handled None eventsSummary without error")
    print(f"    Licking count: {pet.dailyLickingCount} (should be 0)")
except Exception as e:
    print(f"  ✗ Failed with error: {e}")

# Test methods exist
print("\nChecking methods:")
methods = ['updateBehaviorStats', 'setBehaviorStatsFromTrends', '_parseTimelineSegments']
for method in methods:
    exists = hasattr(pet, method)
    status = "✓" if exists else "✗"
    print(f"  {status} {method}: {'exists' if exists else 'MISSING'}")

# Test getPetHealthTrends function exists
print("\nChecking query functions:")
exists = hasattr(query, 'getPetHealthTrends')
status = "✓" if exists else "✗"
print(f"  {status} getPetHealthTrends: {'exists' if exists else 'MISSING'}")

print("\n✅ All tests completed!")