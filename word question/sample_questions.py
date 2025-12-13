#!/usr/bin/env python3
"""
Sample Questions Data
=====================
Use this file for testing the document generator without PDF extraction.

To use:
1. Comment out PDF extraction in main script
2. Import this data: from sample_questions import SAMPLE_QUESTIONS
3. Pass SAMPLE_QUESTIONS to create_document() function
"""

# Sample questions from KVS PGT 2013 (Q101-105)
SAMPLE_QUESTIONS = [
    {
        'question': [
            'When the object making the sound is moving towards you, the frequency goes up due to the waves getting pushed more tightly together. The opposite happens when the object moves away from you and the pitch goes down. This phenomenon is called:'
        ],
        'options': [
            'Band width',
            'Doppler effect',
            'Sound refraction',
            'Vibrations'
        ],
        'correct_idx': 1,
        'solution': [
            'The Doppler effect or Doppler shift is the change in frequency of a wave in relation to an observer who is moving relative to the wave source.'
        ],
        'has_diagram': False
    },
    {
        'question': [
            'Even when the screen is completely dark while the film is in motion, commercial motion pictures use:'
        ],
        'options': [
            '32 frames per second or 102 screen illuminations per second',
            '72 frames per second or 234 screen illuminations per second',
            '8 frames per second or 32 screen illuminations per second',
            '24 frames per second or 72 screen illuminations per second'
        ],
        'correct_idx': 3,
        'solution': [
            'Motion picture, also called film or movie, is a series of still photographs on film, projected in rapid succession onto a screen by means of light. A screen at the rate of at least 16 illuminations per second, but commercial motion pictures use 24 frames per second or 72 screen illuminations per second.'
        ],
        'has_diagram': False
    },
    {
        'question': [
            'Internet Control Message Protocol (ICMP):'
        ],
        'options': [
            'Allows gateways to send error control messages to other gateways or hosts',
            'Provides communication between the Internet Protocol Software on one machine and the Internet Protocol Software on another',
            'Only reports error conditions to the original source, the source must relate errors to individual application programs and take action to correct the problem',
            'All of these'
        ],
        'correct_idx': 3,
        'solution': [
            'ICMP stands for Internet Control Message Protocol. It is one of the main protocols of the internet protocol suite. It is used by network devices, like routers, to send error messages indicating that a requested service is not available or that a host or router could not be reached.'
        ],
        'has_diagram': False
    },
    {
        'question': [
            '______ refers to those attributes of a system visible to a programmer or, put another way, those attributes that have a direct impact on the logical execution of a program.'
        ],
        'options': [
            'Computer organization',
            'Computer architecture',
            'Microprocessor',
            'Bus'
        ],
        'correct_idx': 1,
        'solution': [
            'Computer architecture refers to those attributes of a system visible to a programmer or, put another way, those attributes that have a direct impact on the logical execution of a program.'
        ],
        'has_diagram': False
    },
    {
        'question': [
            'How many characters does an escape sequence (\\On, \\Hn, \\n, \\f) in C++ consume?'
        ],
        'options': [
            '1',
            '3',
            '2',
            'None of these'
        ],
        'correct_idx': 0,
        'solution': [
            'Escape sequences are primarily used to represent actions like carriage returns and tab movements. Although an escape sequence contains two or more characters, it represents a single character. Therefore, an escape sequence in C++ consumes 1 character.'
        ],
        'has_diagram': False
    },
]

# Test function
if __name__ == "__main__":
    print(f"Sample Questions: {len(SAMPLE_QUESTIONS)}")
    print(f"Question 1: {SAMPLE_QUESTIONS[0]['question'][0][:50]}...")
    print(f"Correct answers: {[q['correct_idx'] for q in SAMPLE_QUESTIONS]}")
