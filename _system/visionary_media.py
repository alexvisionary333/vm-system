"""
VISIONARY MEDIA — Branded PDF generator
=======================================

TWO WAYS TO USE THIS

1) Markdown mode (what the team should use):
       python visionary_media.py proposal.md
   Reads front-matter + markdown, writes a branded PDF next to it.
   You never touch this file.

2) Inline mode (for Claude / one-offs):
   Edit the CONFIG block below and run:
       python visionary_media.py

IMAGES: put screenshots in an ./images folder next to your .md and
reference them normally:  ![Caption text](images/perplexity-category.png)
"""
from pathlib import Path
import re, os, subprocess, sys, datetime


# ============================================================================
# CONFIG — inline mode only. Markdown mode overrides all of this.
# ============================================================================

DOC_TITLE     = "AI Visibility"          # eyebrow. 1-3 words.
HEADLINE      = "Replace me"             # the outcome, in their language.
CLIENT_NAME   = "Client Name"
DOC_DATE      = ""                       # blank = today
VALID_THROUGH = ""                       # blank = today + 14 days

# Body as HTML (inline mode). Classes available:
#   <p class="lead">             serif opening paragraph
#   <div class="callout">        navy left-rule aside  (markdown: > blockquote)
#   <div class="pullquote">      serif italic quote + <cite>Name, Role</cite>
#   <table class="pricing">      centred option columns; <tr class="total">
#   <figure><img src="..."><figcaption><strong>Fig 1.</strong> …</figcaption></figure>
#   <div class="signature">      acceptance block
#   <span class="up|down|zero">  navy / red value emphasis
#   <div class="page-break">     force a new page
#
# BRAND TOKENS live in the :root block of TEMPLATE_HTML:
#   --ink #17171B   --paper #FBF9F5   --navy #1B3A5C   --alert #9C3226
# Change --navy in ONE place to swap the accent everywhere.
CONTENT_HTML = """
<h1>Section</h1>
<p>Body copy.</p>
"""

OUTPUT_PATH = "/mnt/user-data/outputs/document.pdf"



# ============================================================================
# EMBEDDED ASSETS — do not modify
# ============================================================================

LOGO_SVG = """<svg version="1.0" xmlns="http://www.w3.org/2000/svg"
 width="1025.764398pt" height="524.813769pt" viewBox="0 0 1025.764398 524.813769"
 preserveAspectRatio="xMidYMid meet">
<g transform="translate(-16.000000,543.855054) scale(0.100000,-0.100000)"
fill="#000000" stroke="none">
<path d="M5130 5430 c-608 -60 -1161 -458 -1402 -1010 -111 -252 -148 -430
-148 -710 0 -234 34 -414 120 -633 204 -522 707 -940 1258 -1047 639 -124
1269 95 1680 583 156 186 272 405 340 642 48 166 57 240 57 465 -1 196 -3 226
-28 340 -77 355 -248 659 -507 904 -372 349 -861 516 -1370 466z m485 -74
c527 -102 980 -448 1206 -919 112 -236 162 -456 162 -717 0 -232 -30 -395
-110 -605 -95 -251 -274 -498 -491 -678 -567 -472 -1395 -516 -2005 -105 -48
32 -100 69 -115 82 -15 13 -52 46 -83 72 -164 144 -319 359 -410 569 -85 199
-126 378 -135 600 -20 458 157 908 485 1236 269 268 587 422 996 483 68 10
423 -3 500 -18z"/>
<path d="M6154 4613 c-60 -70 -111 -130 -114 -133 -34 -29 -130 -155 -130
-170 0 -52 43 -15 216 186 143 165 176 209 168 222 -6 9 -15 17 -21 19 -6 2
-59 -54 -119 -124z"/>
<path d="M4356 4714 c-5 -14 8 -39 34 -64 3 -3 68 -79 144 -170 163 -194 173
-205 192 -189 8 6 14 16 14 21 0 5 -69 90 -152 190 -84 99 -161 191 -171 204
-21 28 -52 31 -61 8z"/>
<path d="M6234 4387 c-17 -12 -96 -80 -177 -151 -144 -126 -167 -156 -124
-164 14 -3 121 80 167 128 3 3 47 41 98 84 50 43 92 84 92 91 0 29 -26 35 -56
12z"/>
<path d="M4367 4393 c-19 -19 6 -48 136 -155 78 -65 155 -129 171 -143 17 -14
36 -23 44 -20 7 3 16 5 18 5 2 0 4 8 3 18 0 9 -36 46 -80 82 -45 36 -88 72
-97 80 -55 50 -170 140 -179 140 -5 0 -13 -3 -16 -7z"/>
<path d="M6075 4048 c-104 -61 -193 -116 -197 -122 -12 -18 -3 -31 23 -33 37
-3 394 216 394 242 0 11 -7 21 -15 22 -8 2 -100 -47 -205 -109z"/>
<path d="M4357 4136 c-3 -8 2 -21 11 -29 34 -29 346 -201 366 -201 14 -1 22 6
24 19 2 16 -30 39 -179 123 -99 56 -189 102 -199 102 -10 0 -20 -6 -23 -14z"/>
<path d="M6215 3938 c-27 -10 -105 -37 -172 -60 -121 -42 -138 -53 -126 -84 7
-18 -5 -21 195 49 180 63 178 62 178 87 0 27 -19 29 -75 8z"/>
<path d="M4352 3928 c3 -26 30 -38 243 -112 113 -39 127 -42 141 -28 24 24 5
35 -179 101 -188 68 -210 72 -205 39z"/>
<path d="M4352 3768 c-17 -17 -15 -36 6 -42 9 -3 82 -17 162 -30 80 -14 159
-28 176 -31 21 -5 34 -2 44 10 24 29 -8 42 -175 70 -88 14 -169 28 -180 31
-11 3 -26 -1 -33 -8z"/>
<path d="M6180 3765 c-36 -6 -108 -20 -160 -29 -90 -17 -114 -28 -107 -51 6
-19 49 -17 195 10 188 33 184 32 180 58 -4 27 -23 29 -108 12z"/>
<path d="M4354 3595 c-4 -8 -4 -22 0 -30 8 -22 357 -22 376 0 7 8 10 22 6 30
-8 22 -374 23 -382 0z"/>
<path d="M5913 3594 c-14 -37 23 -45 204 -43 178 1 203 7 189 44 -4 13 -35 15
-196 15 -168 0 -191 -2 -197 -16z"/>
<path d="M4565 3476 c-224 -42 -225 -43 -225 -65 0 -10 7 -21 14 -24 16 -7
388 58 424 73 12 5 22 18 22 30 0 27 -24 26 -235 -14z"/>
<path d="M5854 3495 c-4 -9 -2 -21 4 -27 20 -20 398 -83 428 -71 23 8 16 42
-8 47 -26 6 -337 57 -385 64 -24 3 -34 0 -39 -13z"/>
<path d="M4710 3389 c-223 -83 -245 -93 -245 -114 0 -13 8 -21 20 -22 11 -1
101 28 199 65 177 66 219 91 186 112 -20 13 -7 16 -160 -41z"/>
<path d="M5773 3433 c-19 -7 -16 -31 5 -42 10 -5 81 -32 157 -60 77 -29 150
-56 163 -61 46 -20 83 -3 63 28 -6 10 -353 143 -369 141 -4 0 -13 -3 -19 -6z"/>
<path d="M4810 3316 c-47 -30 -108 -68 -136 -85 -28 -16 -58 -37 -67 -46 -18
-18 -12 -45 10 -45 8 0 84 43 169 96 111 69 154 101 152 113 -6 31 -43 21
-128 -33z"/>
<path d="M5713 3354 c-3 -8 -1 -20 4 -25 23 -23 309 -179 323 -177 8 2 15 12
15 22 0 19 -34 42 -211 144 -97 55 -121 62 -131 36z"/>
<path d="M4815 3200 c-77 -66 -141 -128 -143 -138 -6 -41 28 -31 100 29 229
190 232 193 225 212 -4 10 -14 17 -24 17 -10 -1 -81 -54 -158 -120z"/>
<path d="M5660 3287 c0 -18 32 -51 132 -136 128 -107 159 -124 166 -90 3 15
-37 53 -213 207 -55 48 -85 54 -85 19z"/>
<path d="M5312 3260 c-12 -16 -22 -36 -22 -45 0 -20 28 -31 43 -16 8 8 15 6
29 -6 14 -13 20 -13 33 -3 20 17 19 24 -7 65 -28 43 -48 44 -76 5z"/>
<path d="M5600 3245 c-14 -17 -17 -12 120 -178 52 -63 103 -117 113 -120 22
-7 33 17 21 43 -12 26 -223 270 -233 270 -5 0 -14 -7 -21 -15z"/>
<path d="M4979 3218 c-13 -17 -62 -81 -110 -141 -72 -91 -86 -114 -78 -129 17
-31 35 -20 92 55 30 39 81 105 112 145 32 42 54 80 51 88 -9 24 -44 15 -67
-18z"/>
<path d="M5074 3202 c-19 -12 -194 -313 -194 -332 0 -22 13 -32 32 -25 19 8
200 321 196 341 -4 20 -18 27 -34 16z"/>
<path d="M5550 3200 c-13 -8 -3 -33 60 -156 99 -193 106 -204 130 -204 29 0
26 29 -11 97 -17 32 -47 90 -67 128 -44 87 -80 145 -90 145 -4 0 -14 -5 -22
-10z"/>
<path d="M5133 3127 c-25 -32 -134 -353 -126 -373 7 -20 39 -18 48 4 11 27
125 353 125 357 0 3 -9 9 -19 14 -13 8 -22 7 -28 -2z"/>
<path d="M5474 3117 c-6 -17 121 -368 138 -378 14 -9 38 7 38 24 0 9 -64 188
-122 340 -11 29 -45 37 -54 14z"/>
<path d="M5400 3045 c-6 -7 -9 -24 -6 -37 3 -12 21 -108 41 -213 44 -231 42
-225 65 -225 30 0 31 25 5 158 -14 70 -30 154 -36 187 -19 101 -29 133 -43
138 -8 3 -20 0 -26 -8z"/>
<path d="M5205 3038 c-12 -36 -76 -394 -73 -412 2 -13 10 -21 23 -21 23 0 25
8 75 269 16 87 27 162 24 167 -8 13 -44 11 -49 -3z"/>
<path d="M5306 2938 c-3 -7 -6 -122 -9 -256 -3 -222 -2 -244 14 -252 11 -7 20
-6 27 3 5 7 11 119 13 262 l4 250 -23 3 c-12 2 -24 -3 -26 -10z"/>
<path d="M9217 1540 c-15 -5 -57 -12 -92 -15 -75 -8 -94 -29 -35 -39 65 -10
70 -26 70 -223 0 -95 -3 -173 -6 -173 -3 0 -20 11 -37 24 -82 60 -206 73 -292
28 -55 -28 -114 -88 -138 -142 -29 -63 -35 -191 -12 -259 40 -122 147 -205
262 -203 69 1 111 16 177 61 25 17 47 31 50 31 3 0 6 -21 6 -46 l0 -47 53 7
c28 3 71 6 95 6 35 0 42 3 42 20 0 17 -7 20 -38 20 -32 0 -41 5 -50 25 -9 19
-12 157 -12 480 0 250 -3 455 -7 454 -5 0 -21 -4 -36 -9z m-131 -448 c76 -39
74 -33 74 -234 l0 -181 -34 -32 c-49 -45 -96 -65 -159 -65 -70 0 -129 40 -160
108 -26 58 -36 232 -17 295 14 47 53 103 84 119 56 30 143 26 212 -10z"/>
<path d="M9506 1529 c-35 -27 -37 -90 -4 -113 77 -54 159 44 93 109 -30 30
-54 31 -89 4z"/>
<path d="M1302 1517 c-12 -13 -22 -36 -22 -51 0 -29 39 -76 64 -76 28 0 64 22
75 47 34 74 -62 139 -117 80z"/>
<path d="M2161 1514 c-34 -43 -26 -86 20 -109 40 -21 56 -19 84 11 30 33 32
63 4 98 -15 19 -30 26 -54 26 -24 0 -39 -7 -54 -26z"/>
<path d="M6620 1516 c0 -9 19 -16 59 -20 101 -12 96 13 96 -430 0 -348 -2
-384 -18 -409 -22 -34 -58 -58 -100 -66 -18 -4 -32 -13 -32 -21 0 -13 29 -15
173 -18 167 -2 172 -2 172 18 0 15 -7 20 -27 20 -39 0 -89 33 -110 72 -16 29
-18 71 -21 391 -2 196 0 357 5 357 4 0 26 -42 47 -93 22 -50 52 -119 66 -152
15 -33 58 -127 95 -210 151 -338 182 -400 196 -400 16 0 34 34 112 215 30 69
97 222 149 340 52 118 103 234 113 257 11 24 22 38 25 33 9 -15 13 -510 4
-646 -9 -145 -21 -164 -101 -166 -44 -1 -53 -4 -53 -20 0 -17 14 -18 230 -18
221 0 230 1 230 20 0 16 -8 19 -61 22 -54 3 -64 6 -83 31 -20 27 -21 43 -24
333 -5 353 2 484 27 515 12 15 32 22 79 26 43 4 62 10 62 19 0 11 -30 14 -148
14 l-149 0 -146 -332 c-80 -183 -160 -364 -177 -403 l-32 -70 -33 70 c-18 39
-58 126 -88 195 -30 69 -68 154 -84 190 -16 36 -58 129 -93 208 l-64 142 -148
0 c-119 0 -148 -3 -148 -14z"/>
<path d="M160 1506 c0 -8 16 -15 41 -19 60 -8 89 -42 144 -170 26 -62 59 -136
72 -165 13 -29 51 -117 85 -195 190 -444 190 -443 220 -432 14 5 26 34 146
320 87 211 161 385 198 467 19 43 34 81 34 87 0 18 74 82 102 88 15 3 28 12
28 19 0 11 -29 14 -150 14 -127 0 -150 -2 -150 -15 0 -10 10 -15 31 -15 21 0
40 -10 61 -30 27 -27 30 -35 24 -71 -6 -39 -101 -280 -216 -549 -34 -80 -63
-146 -64 -147 -2 -2 -72 155 -151 342 -24 55 -62 143 -85 195 -89 203 -94 231
-43 251 13 5 40 9 59 9 24 0 34 5 34 15 0 13 -30 15 -210 15 -171 0 -210 -3
-210 -14z"/>
<path d="M1335 1149 c-38 -10 -82 -19 -97 -19 -25 0 -46 -15 -35 -26 3 -3 22
-7 43 -10 49 -6 61 -22 70 -92 10 -84 -1 -379 -15 -396 -7 -8 -31 -16 -54 -18
-30 -2 -43 -8 -45 -20 -3 -17 10 -18 157 -18 154 0 161 1 161 20 0 16 -7 20
-36 20 -62 0 -63 4 -64 302 0 147 -3 269 -7 271 -5 2 -39 -4 -78 -14z"/>
<path d="M2240 1157 c-19 -5 -65 -14 -103 -20 -37 -7 -68 -16 -68 -22 0 -5 18
-15 41 -20 23 -6 47 -20 53 -30 8 -13 13 -94 15 -223 3 -174 1 -206 -12 -227
-10 -15 -26 -25 -40 -25 -35 0 -56 -10 -56 -26 0 -11 29 -14 155 -14 129 0
155 2 155 15 0 8 -14 17 -35 21 -19 3 -40 13 -47 22 -10 11 -14 86 -18 287
l-5 271 -35 -9z"/>
<path d="M2740 1159 c-76 -6 -115 -25 -177 -82 -75 -69 -88 -104 -88 -232 0
-124 12 -160 79 -226 65 -64 118 -84 226 -84 86 0 100 3 148 29 106 59 162
157 162 284 0 94 -24 155 -87 219 -76 78 -147 103 -263 92z m129 -50 c74 -41
100 -112 101 -270 0 -115 -19 -187 -60 -226 -77 -72 -202 -69 -271 8 -38 42
-54 115 -53 234 1 194 56 272 193 274 36 1 65 -5 90 -20z"/>
<path d="M3275 1150 c-58 -12 -81 -21 -83 -33 -2 -11 3 -17 17 -17 11 0 31 -5
44 -11 33 -15 37 -44 37 -264 0 -206 -6 -227 -60 -235 -23 -3 -36 -11 -38 -23
-3 -16 7 -17 145 -15 124 3 148 5 148 18 0 9 -11 16 -30 18 -63 7 -65 15 -65
228 l0 192 54 50 c69 63 135 79 196 47 55 -28 60 -53 60 -280 0 -230 -1 -235
-64 -235 -29 0 -36 -4 -36 -20 0 -19 7 -20 144 -20 96 0 147 4 152 11 8 14
-14 29 -42 29 -44 0 -49 20 -54 249 -6 247 -11 266 -82 302 -89 45 -199 23
-288 -57 l-38 -35 -7 43 c-9 58 -15 78 -23 77 -4 -1 -43 -9 -87 -19z"/>
<path d="M4200 1159 c-72 -6 -120 -27 -156 -67 -46 -52 -40 -102 12 -102 25 0
48 28 59 72 12 48 45 68 112 69 103 2 142 -33 143 -127 l0 -60 -92 -38 c-192
-78 -276 -145 -285 -229 -5 -51 11 -84 57 -115 30 -21 44 -23 95 -19 59 4 134
35 197 79 l27 19 17 -36 c9 -20 26 -42 38 -50 27 -20 106 -19 134 1 20 14 52
72 52 95 0 21 -27 6 -37 -21 -13 -33 -54 -50 -78 -30 -12 10 -15 43 -15 174
-1 221 -11 290 -47 328 -48 51 -116 68 -233 57z m148 -499 c-40 -34 -121 -70
-155 -70 -102 0 -112 155 -15 227 35 26 129 74 162 83 l25 6 3 -113 c3 -108 1
-115 -20 -133z"/>
<path d="M5036 1162 c-40 -5 -101 -47 -135 -94 l-29 -39 -6 53 c-11 88 -8 88
-183 42 -7 -2 -13 -10 -13 -19 0 -10 10 -15 33 -15 64 0 67 -10 67 -257 0
-241 1 -239 -60 -245 -24 -2 -36 -9 -38 -21 -3 -16 8 -17 152 -15 158 3 195
13 121 33 -67 17 -65 10 -65 194 0 93 3 183 7 201 4 20 25 53 53 82 60 62 87
64 124 7 22 -32 32 -40 53 -37 33 4 48 27 39 61 -12 51 -57 76 -120 69z"/>
<path d="M8206 1156 c-67 -25 -138 -99 -166 -174 -25 -65 -27 -188 -4 -254 19
-57 72 -120 127 -152 83 -48 210 -51 282 -6 41 25 95 85 95 105 0 25 -24 17
-42 -14 -9 -16 -35 -42 -58 -57 -34 -22 -53 -28 -103 -28 -136 -1 -194 83
-200 289 l-2 80 208 3 207 2 -6 28 c-17 71 -67 138 -128 169 -43 22 -161 27
-210 9z m154 -34 c38 -18 54 -45 65 -104 l7 -38 -147 0 c-142 0 -146 1 -141
20 3 11 9 30 12 43 14 49 79 97 134 97 19 0 51 -8 70 -18z"/>
<path d="M9552 1159 c-18 -6 -59 -13 -90 -17 -43 -5 -58 -11 -60 -25 -3 -13 4
-17 30 -17 19 0 43 -6 54 -14 18 -13 19 -30 22 -235 3 -211 2 -221 -17 -240
-13 -13 -34 -21 -56 -21 -24 0 -35 -5 -35 -15 0 -13 25 -15 161 -15 124 0 160
3 157 13 -3 6 -18 14 -34 17 -16 3 -38 10 -49 17 -19 11 -20 24 -23 287 -2
206 -6 276 -15 275 -7 0 -27 -5 -45 -10z"/>
<path d="M9946 1155 c-55 -19 -88 -45 -108 -85 -23 -45 -9 -72 35 -68 28 3 33
9 52 57 15 41 28 58 50 67 66 29 172 5 194 -42 16 -36 15 -144 -2 -144 -23 0
-191 -77 -249 -113 -62 -40 -105 -86 -114 -123 -24 -96 74 -179 184 -155 46
10 156 63 167 82 12 19 31 8 43 -24 15 -42 52 -62 109 -61 49 1 83 26 104 76
9 21 9 32 1 40 -8 8 -13 6 -18 -8 -12 -34 -36 -54 -64 -54 -37 0 -40 13 -40
217 0 211 -9 262 -55 302 -19 16 -51 35 -72 40 -53 15 -171 13 -217 -4z m234
-354 l0 -120 -36 -27 c-20 -15 -59 -35 -87 -45 -90 -30 -142 10 -134 104 6 66
47 108 162 163 50 24 91 44 93 44 1 0 2 -54 2 -119z"/>
<path d="M1683 1140 c-45 -30 -77 -100 -71 -155 8 -66 44 -104 165 -173 111
-63 143 -95 143 -146 0 -61 -48 -106 -115 -106 -67 0 -124 47 -160 133 -9 21
-20 35 -25 32 -6 -3 -10 -49 -10 -101 0 -77 3 -94 15 -94 8 0 15 6 15 13 0 7
6 21 13 31 12 17 15 17 52 -8 49 -33 74 -40 134 -34 132 13 194 168 113 282
-19 28 -53 53 -123 90 -119 64 -136 76 -149 110 -23 61 22 116 96 116 55 0 94
-32 130 -105 14 -30 30 -52 35 -49 5 3 9 46 9 95 0 87 -1 89 -20 79 -11 -6
-20 -17 -20 -25 0 -22 -20 -18 -47 7 -35 33 -136 37 -180 8z"/>
<path d="M5170 1125 c0 -8 8 -15 18 -15 51 0 72 -38 287 -505 l32 -70 -37 -90
c-35 -85 -40 -92 -91 -122 -68 -40 -89 -61 -89 -88 0 -54 58 -60 104 -12 29
31 57 89 150 317 214 524 237 570 287 570 11 0 19 7 19 15 0 13 -16 15 -102
13 -106 -3 -126 -14 -65 -34 44 -15 45 -38 3 -136 -19 -46 -53 -129 -77 -186
-23 -56 -45 -104 -49 -107 -4 -2 -20 24 -35 58 -16 34 -57 122 -92 195 -35 73
-63 139 -63 146 0 19 22 36 47 36 14 0 23 6 23 15 0 13 -22 15 -135 15 -113 0
-135 -2 -135 -15z"/>
</g>
</svg>"""

LOGO_MARK_SVG = """<svg version="1.0" xmlns="http://www.w3.org/2000/svg"
 width="100%" height="100%" viewBox="328.3 -13.8 372.2 371.3"
 preserveAspectRatio="xMidYMid meet">
<g transform="translate(-16.000000,543.855054) scale(0.100000,-0.100000)"
fill="#000000" stroke="none">
<path d="M5130 5430 c-608 -60 -1161 -458 -1402 -1010 -111 -252 -148 -430
-148 -710 0 -234 34 -414 120 -633 204 -522 707 -940 1258 -1047 639 -124
1269 95 1680 583 156 186 272 405 340 642 48 166 57 240 57 465 -1 196 -3 226
-28 340 -77 355 -248 659 -507 904 -372 349 -861 516 -1370 466z m485 -74
c527 -102 980 -448 1206 -919 112 -236 162 -456 162 -717 0 -232 -30 -395
-110 -605 -95 -251 -274 -498 -491 -678 -567 -472 -1395 -516 -2005 -105 -48
32 -100 69 -115 82 -15 13 -52 46 -83 72 -164 144 -319 359 -410 569 -85 199
-126 378 -135 600 -20 458 157 908 485 1236 269 268 587 422 996 483 68 10
423 -3 500 -18z"/>
<path d="M6154 4613 c-60 -70 -111 -130 -114 -133 -34 -29 -130 -155 -130
-170 0 -52 43 -15 216 186 143 165 176 209 168 222 -6 9 -15 17 -21 19 -6 2
-59 -54 -119 -124z"/>
<path d="M4356 4714 c-5 -14 8 -39 34 -64 3 -3 68 -79 144 -170 163 -194 173
-205 192 -189 8 6 14 16 14 21 0 5 -69 90 -152 190 -84 99 -161 191 -171 204
-21 28 -52 31 -61 8z"/>
<path d="M6234 4387 c-17 -12 -96 -80 -177 -151 -144 -126 -167 -156 -124
-164 14 -3 121 80 167 128 3 3 47 41 98 84 50 43 92 84 92 91 0 29 -26 35 -56
12z"/>
<path d="M4367 4393 c-19 -19 6 -48 136 -155 78 -65 155 -129 171 -143 17 -14
36 -23 44 -20 7 3 16 5 18 5 2 0 4 8 3 18 0 9 -36 46 -80 82 -45 36 -88 72
-97 80 -55 50 -170 140 -179 140 -5 0 -13 -3 -16 -7z"/>
<path d="M6075 4048 c-104 -61 -193 -116 -197 -122 -12 -18 -3 -31 23 -33 37
-3 394 216 394 242 0 11 -7 21 -15 22 -8 2 -100 -47 -205 -109z"/>
<path d="M4357 4136 c-3 -8 2 -21 11 -29 34 -29 346 -201 366 -201 14 -1 22 6
24 19 2 16 -30 39 -179 123 -99 56 -189 102 -199 102 -10 0 -20 -6 -23 -14z"/>
<path d="M6215 3938 c-27 -10 -105 -37 -172 -60 -121 -42 -138 -53 -126 -84 7
-18 -5 -21 195 49 180 63 178 62 178 87 0 27 -19 29 -75 8z"/>
<path d="M4352 3928 c3 -26 30 -38 243 -112 113 -39 127 -42 141 -28 24 24 5
35 -179 101 -188 68 -210 72 -205 39z"/>
<path d="M4352 3768 c-17 -17 -15 -36 6 -42 9 -3 82 -17 162 -30 80 -14 159
-28 176 -31 21 -5 34 -2 44 10 24 29 -8 42 -175 70 -88 14 -169 28 -180 31
-11 3 -26 -1 -33 -8z"/>
<path d="M6180 3765 c-36 -6 -108 -20 -160 -29 -90 -17 -114 -28 -107 -51 6
-19 49 -17 195 10 188 33 184 32 180 58 -4 27 -23 29 -108 12z"/>
<path d="M4354 3595 c-4 -8 -4 -22 0 -30 8 -22 357 -22 376 0 7 8 10 22 6 30
-8 22 -374 23 -382 0z"/>
<path d="M5913 3594 c-14 -37 23 -45 204 -43 178 1 203 7 189 44 -4 13 -35 15
-196 15 -168 0 -191 -2 -197 -16z"/>
<path d="M4565 3476 c-224 -42 -225 -43 -225 -65 0 -10 7 -21 14 -24 16 -7
388 58 424 73 12 5 22 18 22 30 0 27 -24 26 -235 -14z"/>
<path d="M5854 3495 c-4 -9 -2 -21 4 -27 20 -20 398 -83 428 -71 23 8 16 42
-8 47 -26 6 -337 57 -385 64 -24 3 -34 0 -39 -13z"/>
<path d="M4710 3389 c-223 -83 -245 -93 -245 -114 0 -13 8 -21 20 -22 11 -1
101 28 199 65 177 66 219 91 186 112 -20 13 -7 16 -160 -41z"/>
<path d="M5773 3433 c-19 -7 -16 -31 5 -42 10 -5 81 -32 157 -60 77 -29 150
-56 163 -61 46 -20 83 -3 63 28 -6 10 -353 143 -369 141 -4 0 -13 -3 -19 -6z"/>
<path d="M4810 3316 c-47 -30 -108 -68 -136 -85 -28 -16 -58 -37 -67 -46 -18
-18 -12 -45 10 -45 8 0 84 43 169 96 111 69 154 101 152 113 -6 31 -43 21
-128 -33z"/>
<path d="M5713 3354 c-3 -8 -1 -20 4 -25 23 -23 309 -179 323 -177 8 2 15 12
15 22 0 19 -34 42 -211 144 -97 55 -121 62 -131 36z"/>
<path d="M4815 3200 c-77 -66 -141 -128 -143 -138 -6 -41 28 -31 100 29 229
190 232 193 225 212 -4 10 -14 17 -24 17 -10 -1 -81 -54 -158 -120z"/>
<path d="M5660 3287 c0 -18 32 -51 132 -136 128 -107 159 -124 166 -90 3 15
-37 53 -213 207 -55 48 -85 54 -85 19z"/>
<path d="M5312 3260 c-12 -16 -22 -36 -22 -45 0 -20 28 -31 43 -16 8 8 15 6
29 -6 14 -13 20 -13 33 -3 20 17 19 24 -7 65 -28 43 -48 44 -76 5z"/>
<path d="M5600 3245 c-14 -17 -17 -12 120 -178 52 -63 103 -117 113 -120 22
-7 33 17 21 43 -12 26 -223 270 -233 270 -5 0 -14 -7 -21 -15z"/>
<path d="M4979 3218 c-13 -17 -62 -81 -110 -141 -72 -91 -86 -114 -78 -129 17
-31 35 -20 92 55 30 39 81 105 112 145 32 42 54 80 51 88 -9 24 -44 15 -67
-18z"/>
<path d="M5074 3202 c-19 -12 -194 -313 -194 -332 0 -22 13 -32 32 -25 19 8
200 321 196 341 -4 20 -18 27 -34 16z"/>
<path d="M5550 3200 c-13 -8 -3 -33 60 -156 99 -193 106 -204 130 -204 29 0
26 29 -11 97 -17 32 -47 90 -67 128 -44 87 -80 145 -90 145 -4 0 -14 -5 -22
-10z"/>
<path d="M5133 3127 c-25 -32 -134 -353 -126 -373 7 -20 39 -18 48 4 11 27
125 353 125 357 0 3 -9 9 -19 14 -13 8 -22 7 -28 -2z"/>
<path d="M5474 3117 c-6 -17 121 -368 138 -378 14 -9 38 7 38 24 0 9 -64 188
-122 340 -11 29 -45 37 -54 14z"/>
<path d="M5400 3045 c-6 -7 -9 -24 -6 -37 3 -12 21 -108 41 -213 44 -231 42
-225 65 -225 30 0 31 25 5 158 -14 70 -30 154 -36 187 -19 101 -29 133 -43
138 -8 3 -20 0 -26 -8z"/>
<path d="M5205 3038 c-12 -36 -76 -394 -73 -412 2 -13 10 -21 23 -21 23 0 25
8 75 269 16 87 27 162 24 167 -8 13 -44 11 -49 -3z"/>
<path d="M5306 2938 c-3 -7 -6 -122 -9 -256 -3 -222 -2 -244 14 -252 11 -7 20
-6 27 3 5 7 11 119 13 262 l4 250 -23 3 c-12 2 -24 -3 -26 -10z"/>
<path d="M9217 1540 c-15 -5 -57 -12 -92 -15 -75 -8 -94 -29 -35 -39 65 -10
70 -26 70 -223 0 -95 -3 -173 -6 -173 -3 0 -20 11 -37 24 -82 60 -206 73 -292
28 -55 -28 -114 -88 -138 -142 -29 -63 -35 -191 -12 -259 40 -122 147 -205
262 -203 69 1 111 16 177 61 25 17 47 31 50 31 3 0 6 -21 6 -46 l0 -47 53 7
c28 3 71 6 95 6 35 0 42 3 42 20 0 17 -7 20 -38 20 -32 0 -41 5 -50 25 -9 19
-12 157 -12 480 0 250 -3 455 -7 454 -5 0 -21 -4 -36 -9z m-131 -448 c76 -39
74 -33 74 -234 l0 -181 -34 -32 c-49 -45 -96 -65 -159 -65 -70 0 -129 40 -160
108 -26 58 -36 232 -17 295 14 47 53 103 84 119 56 30 143 26 212 -10z"/>
<path d="M9506 1529 c-35 -27 -37 -90 -4 -113 77 -54 159 44 93 109 -30 30
-54 31 -89 4z"/>
<path d="M1302 1517 c-12 -13 -22 -36 -22 -51 0 -29 39 -76 64 -76 28 0 64 22
75 47 34 74 -62 139 -117 80z"/>
<path d="M2161 1514 c-34 -43 -26 -86 20 -109 40 -21 56 -19 84 11 30 33 32
63 4 98 -15 19 -30 26 -54 26 -24 0 -39 -7 -54 -26z"/>
<path d="M6620 1516 c0 -9 19 -16 59 -20 101 -12 96 13 96 -430 0 -348 -2
-384 -18 -409 -22 -34 -58 -58 -100 -66 -18 -4 -32 -13 -32 -21 0 -13 29 -15
173 -18 167 -2 172 -2 172 18 0 15 -7 20 -27 20 -39 0 -89 33 -110 72 -16 29
-18 71 -21 391 -2 196 0 357 5 357 4 0 26 -42 47 -93 22 -50 52 -119 66 -152
15 -33 58 -127 95 -210 151 -338 182 -400 196 -400 16 0 34 34 112 215 30 69
97 222 149 340 52 118 103 234 113 257 11 24 22 38 25 33 9 -15 13 -510 4
-646 -9 -145 -21 -164 -101 -166 -44 -1 -53 -4 -53 -20 0 -17 14 -18 230 -18
221 0 230 1 230 20 0 16 -8 19 -61 22 -54 3 -64 6 -83 31 -20 27 -21 43 -24
333 -5 353 2 484 27 515 12 15 32 22 79 26 43 4 62 10 62 19 0 11 -30 14 -148
14 l-149 0 -146 -332 c-80 -183 -160 -364 -177 -403 l-32 -70 -33 70 c-18 39
-58 126 -88 195 -30 69 -68 154 -84 190 -16 36 -58 129 -93 208 l-64 142 -148
0 c-119 0 -148 -3 -148 -14z"/>
<path d="M160 1506 c0 -8 16 -15 41 -19 60 -8 89 -42 144 -170 26 -62 59 -136
72 -165 13 -29 51 -117 85 -195 190 -444 190 -443 220 -432 14 5 26 34 146
320 87 211 161 385 198 467 19 43 34 81 34 87 0 18 74 82 102 88 15 3 28 12
28 19 0 11 -29 14 -150 14 -127 0 -150 -2 -150 -15 0 -10 10 -15 31 -15 21 0
40 -10 61 -30 27 -27 30 -35 24 -71 -6 -39 -101 -280 -216 -549 -34 -80 -63
-146 -64 -147 -2 -2 -72 155 -151 342 -24 55 -62 143 -85 195 -89 203 -94 231
-43 251 13 5 40 9 59 9 24 0 34 5 34 15 0 13 -30 15 -210 15 -171 0 -210 -3
-210 -14z"/>
<path d="M1335 1149 c-38 -10 -82 -19 -97 -19 -25 0 -46 -15 -35 -26 3 -3 22
-7 43 -10 49 -6 61 -22 70 -92 10 -84 -1 -379 -15 -396 -7 -8 -31 -16 -54 -18
-30 -2 -43 -8 -45 -20 -3 -17 10 -18 157 -18 154 0 161 1 161 20 0 16 -7 20
-36 20 -62 0 -63 4 -64 302 0 147 -3 269 -7 271 -5 2 -39 -4 -78 -14z"/>
<path d="M2240 1157 c-19 -5 -65 -14 -103 -20 -37 -7 -68 -16 -68 -22 0 -5 18
-15 41 -20 23 -6 47 -20 53 -30 8 -13 13 -94 15 -223 3 -174 1 -206 -12 -227
-10 -15 -26 -25 -40 -25 -35 0 -56 -10 -56 -26 0 -11 29 -14 155 -14 129 0
155 2 155 15 0 8 -14 17 -35 21 -19 3 -40 13 -47 22 -10 11 -14 86 -18 287
l-5 271 -35 -9z"/>
<path d="M2740 1159 c-76 -6 -115 -25 -177 -82 -75 -69 -88 -104 -88 -232 0
-124 12 -160 79 -226 65 -64 118 -84 226 -84 86 0 100 3 148 29 106 59 162
157 162 284 0 94 -24 155 -87 219 -76 78 -147 103 -263 92z m129 -50 c74 -41
100 -112 101 -270 0 -115 -19 -187 -60 -226 -77 -72 -202 -69 -271 8 -38 42
-54 115 -53 234 1 194 56 272 193 274 36 1 65 -5 90 -20z"/>
<path d="M3275 1150 c-58 -12 -81 -21 -83 -33 -2 -11 3 -17 17 -17 11 0 31 -5
44 -11 33 -15 37 -44 37 -264 0 -206 -6 -227 -60 -235 -23 -3 -36 -11 -38 -23
-3 -16 7 -17 145 -15 124 3 148 5 148 18 0 9 -11 16 -30 18 -63 7 -65 15 -65
228 l0 192 54 50 c69 63 135 79 196 47 55 -28 60 -53 60 -280 0 -230 -1 -235
-64 -235 -29 0 -36 -4 -36 -20 0 -19 7 -20 144 -20 96 0 147 4 152 11 8 14
-14 29 -42 29 -44 0 -49 20 -54 249 -6 247 -11 266 -82 302 -89 45 -199 23
-288 -57 l-38 -35 -7 43 c-9 58 -15 78 -23 77 -4 -1 -43 -9 -87 -19z"/>
<path d="M4200 1159 c-72 -6 -120 -27 -156 -67 -46 -52 -40 -102 12 -102 25 0
48 28 59 72 12 48 45 68 112 69 103 2 142 -33 143 -127 l0 -60 -92 -38 c-192
-78 -276 -145 -285 -229 -5 -51 11 -84 57 -115 30 -21 44 -23 95 -19 59 4 134
35 197 79 l27 19 17 -36 c9 -20 26 -42 38 -50 27 -20 106 -19 134 1 20 14 52
72 52 95 0 21 -27 6 -37 -21 -13 -33 -54 -50 -78 -30 -12 10 -15 43 -15 174
-1 221 -11 290 -47 328 -48 51 -116 68 -233 57z m148 -499 c-40 -34 -121 -70
-155 -70 -102 0 -112 155 -15 227 35 26 129 74 162 83 l25 6 3 -113 c3 -108 1
-115 -20 -133z"/>
<path d="M5036 1162 c-40 -5 -101 -47 -135 -94 l-29 -39 -6 53 c-11 88 -8 88
-183 42 -7 -2 -13 -10 -13 -19 0 -10 10 -15 33 -15 64 0 67 -10 67 -257 0
-241 1 -239 -60 -245 -24 -2 -36 -9 -38 -21 -3 -16 8 -17 152 -15 158 3 195
13 121 33 -67 17 -65 10 -65 194 0 93 3 183 7 201 4 20 25 53 53 82 60 62 87
64 124 7 22 -32 32 -40 53 -37 33 4 48 27 39 61 -12 51 -57 76 -120 69z"/>
<path d="M8206 1156 c-67 -25 -138 -99 -166 -174 -25 -65 -27 -188 -4 -254 19
-57 72 -120 127 -152 83 -48 210 -51 282 -6 41 25 95 85 95 105 0 25 -24 17
-42 -14 -9 -16 -35 -42 -58 -57 -34 -22 -53 -28 -103 -28 -136 -1 -194 83
-200 289 l-2 80 208 3 207 2 -6 28 c-17 71 -67 138 -128 169 -43 22 -161 27
-210 9z m154 -34 c38 -18 54 -45 65 -104 l7 -38 -147 0 c-142 0 -146 1 -141
20 3 11 9 30 12 43 14 49 79 97 134 97 19 0 51 -8 70 -18z"/>
<path d="M9552 1159 c-18 -6 -59 -13 -90 -17 -43 -5 -58 -11 -60 -25 -3 -13 4
-17 30 -17 19 0 43 -6 54 -14 18 -13 19 -30 22 -235 3 -211 2 -221 -17 -240
-13 -13 -34 -21 -56 -21 -24 0 -35 -5 -35 -15 0 -13 25 -15 161 -15 124 0 160
3 157 13 -3 6 -18 14 -34 17 -16 3 -38 10 -49 17 -19 11 -20 24 -23 287 -2
206 -6 276 -15 275 -7 0 -27 -5 -45 -10z"/>
<path d="M9946 1155 c-55 -19 -88 -45 -108 -85 -23 -45 -9 -72 35 -68 28 3 33
9 52 57 15 41 28 58 50 67 66 29 172 5 194 -42 16 -36 15 -144 -2 -144 -23 0
-191 -77 -249 -113 -62 -40 -105 -86 -114 -123 -24 -96 74 -179 184 -155 46
10 156 63 167 82 12 19 31 8 43 -24 15 -42 52 -62 109 -61 49 1 83 26 104 76
9 21 9 32 1 40 -8 8 -13 6 -18 -8 -12 -34 -36 -54 -64 -54 -37 0 -40 13 -40
217 0 211 -9 262 -55 302 -19 16 -51 35 -72 40 -53 15 -171 13 -217 -4z m234
-354 l0 -120 -36 -27 c-20 -15 -59 -35 -87 -45 -90 -30 -142 10 -134 104 6 66
47 108 162 163 50 24 91 44 93 44 1 0 2 -54 2 -119z"/>
<path d="M1683 1140 c-45 -30 -77 -100 -71 -155 8 -66 44 -104 165 -173 111
-63 143 -95 143 -146 0 -61 -48 -106 -115 -106 -67 0 -124 47 -160 133 -9 21
-20 35 -25 32 -6 -3 -10 -49 -10 -101 0 -77 3 -94 15 -94 8 0 15 6 15 13 0 7
6 21 13 31 12 17 15 17 52 -8 49 -33 74 -40 134 -34 132 13 194 168 113 282
-19 28 -53 53 -123 90 -119 64 -136 76 -149 110 -23 61 22 116 96 116 55 0 94
-32 130 -105 14 -30 30 -52 35 -49 5 3 9 46 9 95 0 87 -1 89 -20 79 -11 -6
-20 -17 -20 -25 0 -22 -20 -18 -47 7 -35 33 -136 37 -180 8z"/>
<path d="M5170 1125 c0 -8 8 -15 18 -15 51 0 72 -38 287 -505 l32 -70 -37 -90
c-35 -85 -40 -92 -91 -122 -68 -40 -89 -61 -89 -88 0 -54 58 -60 104 -12 29
31 57 89 150 317 214 524 237 570 287 570 11 0 19 7 19 15 0 13 -16 15 -102
13 -106 -3 -126 -14 -65 -34 44 -15 45 -38 3 -136 -19 -46 -53 -129 -77 -186
-23 -56 -45 -104 -49 -107 -4 -2 -20 24 -35 58 -16 34 -57 122 -92 195 -35 73
-63 139 -63 146 0 19 22 36 47 36 14 0 23 6 23 15 0 13 -22 15 -135 15 -113 0
-135 -2 -135 -15z"/>
</g>
</svg>"""

TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{{DOC_TITLE}}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Instrument+Serif:ital@0;1&family=Cormorant+Garamond:wght@400;500;600&display=swap');

/* =========================================================
   VISIONARY MEDIA — multi-page template
   Strategy: position:fixed repeats elements on every page in WeasyPrint.
   ========================================================= */

@page {
  size: Letter;
  margin: 26mm 21mm 22mm 21mm;
  background: #FBF9F5;
  @bottom-right {
    content: counter(page);
    font-family: 'Instrument Sans', sans-serif;
    font-size: 7.5pt;
    letter-spacing: 0.5px;
    color: #9C968C;
    margin-bottom: 9mm;
  }
}

:root {
  --ink:    #17171B;
  --paper:  #FBF9F5;
  --navy:   #1B3A5C;
  --navy-2: #2E5580;
  --muted:  #6C675E;
  --rule:   #DDD6CB;
  --hair:   #E9E3D9;
  --alert:  #9C3226;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html { background: var(--paper); font-size: 12px; }
body {
  background: var(--paper);
  font-family: 'Instrument Sans', -apple-system, sans-serif;
  font-size: 10pt;
  line-height: 1.62;
  color: var(--ink);
  font-feature-settings: "ss01", "cv01";
}

/* ============ RUNNING HEAD ============ */
.running-head {
  position: fixed;
  top: -15mm; left: 0; right: 0;
  display: flex; align-items: baseline; justify-content: space-between;
  font-size: 7.5pt; letter-spacing: 1.1px;
  color: var(--muted); text-transform: uppercase;
  z-index: 60;
}
.running-head .rh-right {
  display: flex; align-items: center; gap: 2.2mm;
  font-family: 'Cormorant Garamond', serif;
  text-transform: none; letter-spacing: 0.6px; font-size: 9.5pt;
  color: var(--ink);
}
.running-head .rh-mark { width: 4.2mm; }
.running-head .rh-mark img { width: 100%; height: auto; display: block; }

/* ============ FOOTER ============ */
.page-footer {
  position: fixed;
  bottom: -13mm; left: 0; right: 0;
  display: flex; align-items: center; gap: 4mm;
  z-index: 60;
}
.page-footer .mini-mark { width: 5mm; flex-shrink: 0; }
.page-footer .mini-mark img { width: 100%; height: auto; display: block; }
.page-footer .rule { flex-grow: 1; height: 0.3pt; background: var(--rule); }

/* ============ DOC HEAD (page 1) ============ */
.doc-head { margin-bottom: 15mm; page-break-after: avoid; }
.doc-head .doc-logo {
  width: 56mm;
  margin-bottom: 16mm;
}
.doc-head .doc-logo img { width: 100%; height: auto; display: block; }
.doc-head .eyebrow {
  font-size: 7.5pt; letter-spacing: 2px; text-transform: uppercase;
  color: var(--navy); margin-bottom: 7mm; font-weight: 500;
}
.doc-head .headline {
  font-family: 'Instrument Serif', Georgia, serif;
  font-weight: 400; font-size: 34pt; line-height: 1.06;
  letter-spacing: -0.4px; max-width: 148mm; color: var(--ink);
}
.doc-head .meta {
  margin-top: 9mm; padding-top: 4mm;
  border-top: 0.3pt solid var(--rule);
  font-size: 8.5pt; letter-spacing: 0.3px; color: var(--muted);
  display: flex; justify-content: space-between;
}
.doc-head .meta strong { color: var(--ink); font-weight: 600; }

/* ============ CONTENT ============ */
.content { position: relative; z-index: 5; }

.content h1 {
  font-family: 'Instrument Serif', Georgia, serif;
  font-weight: 400; font-size: 20pt; line-height: 1.14;
  margin: 12mm 0 4mm 0; color: var(--ink);
  letter-spacing: -0.1px; page-break-after: avoid;
}
.content h1:first-child { margin-top: 0; }

.content h2 {
  font-weight: 600; font-size: 10.5pt; letter-spacing: -0.05px;
  margin: 7mm 0 2mm 0; color: var(--ink); page-break-after: avoid;
}
.content h3 {
  font-weight: 600; font-size: 7.5pt; letter-spacing: 1.4px;
  text-transform: uppercase; color: var(--navy);
  margin: 6mm 0 2mm 0; page-break-after: avoid;
}

.content p { margin-bottom: 3.4mm; font-size: 10pt; line-height: 1.62; }
.content ul, .content ol { margin: 2.5mm 0 4.5mm 5mm; font-size: 10pt; }
.content li { margin-bottom: 1.6mm; line-height: 1.55; }
.content strong { font-weight: 600; color: var(--ink); }
.content a { color: var(--navy); text-decoration: none; }

.lead {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 15pt !important; line-height: 1.36 !important;
  color: var(--ink); margin-bottom: 6mm !important;
}

/* ============ CALLOUT ============ */
.card, .callout {
  border-left: 0.8mm solid var(--navy);
  padding: 1mm 0 1mm 7mm;
  margin: 6mm 0;
  page-break-inside: avoid;
}
.card h1, .card h2, .card h3,
.callout h1, .callout h2, .callout h3 { margin-top: 0; }
.card p:last-child, .callout p:last-child { margin-bottom: 0; }

/* ============ PULLQUOTE ============ */
.pullquote {
  font-family: 'Instrument Serif', Georgia, serif;
  font-style: italic;
  font-size: 16pt; line-height: 1.32; color: var(--ink);
  margin: 8mm 0 8mm 0; padding-left: 7mm;
  border-left: 0.8mm solid var(--navy);
  page-break-inside: avoid;
}
.pullquote cite {
  display: block; margin-top: 4mm;
  font-family: 'Instrument Sans', sans-serif; font-style: normal;
  font-size: 8pt; letter-spacing: 0.8px; text-transform: uppercase;
  color: var(--muted);
}

/* ============ TABLES (editorial: rules, not fills) ============ */
.content table {
  width: 100%; border-collapse: collapse;
  margin: 5mm 0 6mm 0; font-size: 9pt;
  page-break-inside: avoid;
}
.content table th {
  background: transparent; color: var(--navy);
  font-weight: 600; text-align: left;
  padding: 0 4mm 2.2mm 0; font-size: 7.5pt;
  letter-spacing: 1.3px; text-transform: uppercase;
  border-bottom: 0.8pt solid var(--ink);
}
.content table th:first-child { padding-left: 0; }
.content table td {
  padding: 3mm 4mm 3mm 0;
  border-bottom: 0.3pt solid var(--hair);
  vertical-align: top; line-height: 1.45;
}
.content table td:first-child { font-weight: 500; padding-left: 0; }
.content table tr:last-child td { border-bottom: none; }

.up   { color: var(--navy); font-weight: 600; }
.down { color: var(--alert); font-weight: 600; }
.zero { color: var(--alert); font-weight: 600; }

table.pricing td:not(:first-child),
table.pricing th:not(:first-child) { text-align: center; padding-right: 0; }
table.pricing tr.total td {
  border-top: 0.8pt solid var(--ink);
  border-bottom: none;
  font-weight: 600; padding-top: 3.5mm;
}

/* ============ IMAGES ============ */
figure { margin: 7mm 0 8mm 0; page-break-inside: avoid; }
figure img {
  width: 100%; height: auto; display: block;
  border: 0.3pt solid var(--rule);
}
figure.narrow { max-width: 108mm; }
figure figcaption {
  margin-top: 2.5mm; font-size: 8pt; letter-spacing: 0.2px;
  color: var(--muted); line-height: 1.45;
  padding-left: 0; border-left: none;
}
figure figcaption strong {
  color: var(--navy); font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.9px; font-size: 7.5pt;
}
.content img { max-width: 100%; height: auto; }

/* ============ SIGNATURE ============ */
.signature {
  border-top: 0.8pt solid var(--ink);
  padding-top: 7mm; margin-top: 9mm;
  page-break-inside: avoid;
}
.signature .sig-line {
  margin-top: 4mm; padding-top: 9mm;
  border-bottom: 0.4pt solid var(--ink);
}
.signature .sig-label {
  font-size: 7.5pt; letter-spacing: 1.3px;
  text-transform: uppercase; color: var(--muted);
  margin-top: 2mm;
}
.signature .sig-row { display: flex; gap: 14mm; }
.signature .sig-row > div { flex: 1; }

.draft-stamp {
  position: fixed;
  top: 40%; left: -6mm; right: -6mm;
  transform: rotate(-24deg);
  text-align: center;
  font-family: 'Instrument Sans', sans-serif;
  font-weight: 700; font-size: 62pt; letter-spacing: 10px;
  color: rgba(156, 50, 38, 0.13);
  z-index: 90; pointer-events: none;
}

.page-break { page-break-after: always; }
</style>
</head>
<body>

{{DRAFT_STAMP}}
<!-- RUNNING HEADER (quiet, every page) -->
<div class="running-head">
  <div>{{CLIENT_NAME}} &nbsp;·&nbsp; {{DOC_TITLE}}</div>
  <div class="rh-right"><span class="rh-mark">{{LOGO_MARK_SVG}}</span>Visionary Media</div>
</div>

<!-- FOOTER -->
<div class="page-footer">
  <div class="mini-mark">{{LOGO_MARK_SVG}}</div>
  <div class="rule"></div>
</div>

<!-- DOCUMENT HEAD - page 1 only, flows with content -->
<div class="doc-head">
  <div class="doc-logo">{{LOGO_SVG}}</div>
  <div class="eyebrow">{{DOC_TITLE}}</div>
  <div class="headline">{{HEADLINE}}</div>
  <div class="meta">
    <span>Prepared for <strong>{{CLIENT_NAME}}</strong></span>
    <span>{{DOC_DATE}} &nbsp;·&nbsp; Valid through {{VALID_THROUGH}}</span>
  </div>
</div>

<main class="content">
{{CONTENT_HTML}}
</main>

</body>
</html>
"""


# ============================================================================
# RENDERER
# ============================================================================

def _escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _md_to_html(md_text, base_dir):
    """Markdown -> HTML. Tables, fenced blocks, images, and our own classes."""
    try:
        import markdown
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "markdown", "--break-system-packages", "-q"])
        import markdown

    html = markdown.markdown(
        md_text,
        extensions=["tables", "attr_list", "md_in_html", "sane_lists"],
    )

    # > blockquote  ->  callout panel
    html = html.replace("<blockquote>", '<div class="callout">')
    html = html.replace("</blockquote>", "</div>")

    # bare <img> with alt text -> <figure> + caption
    def figurize(m):
        src_attr, alt = m.group(1), m.group(2)
        p = (Path(base_dir) / src_attr).resolve()
        cap = f"<figcaption>{alt}</figcaption>" if alt.strip() else ""
        return f'<figure><img src="{p.as_uri()}">{cap}</figure>'

    # python-markdown emits img attributes alphabetically — alt BEFORE src —
    # so the old src-first patterns never matched. Every figure silently
    # degraded to WeasyPrint's broken-image alt-text fallback: no image, no
    # <figcaption>, and raw ** markers printed in the client PDF. Match either
    # attribute order. **Bold** inside a caption is honoured here because
    # markdown does not process alt text.
    def _img(tag):
        src = re.search(r'src="([^"]*)"', tag)
        # the second pass must not re-resolve a src the first pass already
        # rewrote to an absolute URI, or the path is joined onto base_dir twice
        if not src or re.match(r'(?i)(file|https?|data):', src.group(1)):
            return tag
        alt = re.search(r'alt="([^"]*)"', tag)
        alt_txt = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>',
                         alt.group(1) if alt else "")
        return figurize(type("M", (), {"group": staticmethod(
            lambda i: src.group(1) if i == 1 else alt_txt)})())

    html = re.sub(r'<p>\s*<img\b[^>]*>\s*</p>',
                  lambda m: _img(re.search(r'<img\b[^>]*>', m.group(0)).group(0)),
                  html)
    html = re.sub(r'<img\b[^>]*>', lambda m: _img(m.group(0)), html)

    # pricing tables: any table whose first header cell is empty
    html = re.sub(r'<table>(\s*<thead>\s*<tr>\s*<th[^>]*>\s*</th>)',
                  r'<table class="pricing">\1', html)
    # a row whose first cell is bold becomes the emphasised total row
    html = re.sub(r'<tr>\s*<td([^>]*)><strong>',
                  r'<tr class="total"><td\1><strong>', html)
    return html


def _parse_front_matter(text):
    """--- key: value --- block at the top of the .md file."""
    meta = {}
    if text.lstrip().startswith("---"):
        _, fm, body = text.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip()
        return meta, body
    return meta, text


_LOGO_CACHE = {}


def _logo_img(svg, width_px, css_class=""):
    """WeasyPrint's SVG renderer mangles this lockup (drops the wordmark and
    mis-maps the viewBox), so rasterise once with cairosvg and embed as PNG."""
    key = (id(svg), width_px)
    if key not in _LOGO_CACHE:
        try:
            import cairosvg
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install",
                                   "cairosvg", "--break-system-packages", "-q"])
            import cairosvg
        import base64, io
        buf = io.BytesIO()
        cairosvg.svg2png(bytestring=svg.encode(), write_to=buf,
                         output_width=width_px)
        _LOGO_CACHE[key] = base64.b64encode(buf.getvalue()).decode()
    cls = f' class="{css_class}"' if css_class else ""
    return f'<img{cls} src="data:image/png;base64,{_LOGO_CACHE[key]}">'


def render(md_path=None, draft=False):
    try:
        from weasyprint import HTML
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "weasyprint", "--break-system-packages", "-q"])
        from weasyprint import HTML

    doc_title, headline = DOC_TITLE, HEADLINE
    client, content = CLIENT_NAME, CONTENT_HTML
    doc_date, valid = DOC_DATE, VALID_THROUGH
    out = OUTPUT_PATH

    if md_path:
        p = Path(md_path)
        raw = p.read_text(encoding="utf-8")
        meta, body = _parse_front_matter(raw)
        doc_title = meta.get("title", doc_title)
        headline  = meta.get("headline", headline)
        client    = meta.get("client", client)
        doc_date  = meta.get("date", "")
        valid     = meta.get("valid_through", "")
        content   = _md_to_html(body, p.parent)
        out = meta.get("output") or str(
            Path("/mnt/user-data/outputs") /
            (p.stem.replace(" ", "-").lower() + ".pdf"))

    today = datetime.date.today()
    if not doc_date:
        doc_date = today.strftime("%B %-d, %Y")
    if not valid:
        valid = (today + datetime.timedelta(days=14)).strftime("%B %-d, %Y")

    html = (TEMPLATE_HTML
            .replace("{{DRAFT_STAMP}}",
                     '<div class="draft-stamp">NOT FOR SEND</div>' if draft else "")
            .replace("{{DOC_TITLE}}", _escape(doc_title))
            .replace("{{HEADLINE}}", _escape(headline))
            .replace("{{CLIENT_NAME}}", _escape(client))
            .replace("{{DOC_DATE}}", _escape(doc_date))
            .replace("{{VALID_THROUGH}}", _escape(valid))
            .replace("{{CONTENT_HTML}}", content)
            .replace("{{LOGO_SVG}}", _logo_img(LOGO_SVG, 1800))
            .replace("{{LOGO_MARK_SVG}}", _logo_img(LOGO_MARK_SVG, 400)))

    os.makedirs(os.path.dirname(out), exist_ok=True)
    HTML(string=html, base_url=str(Path(md_path).parent) if md_path else ".").write_pdf(out)
    print(f"Wrote: {out}")
    return out


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else None,
           draft="--draft" in sys.argv)
