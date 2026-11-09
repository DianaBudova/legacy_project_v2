from copy import deepcopy
from pathlib import Path
import json, re
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path.cwd(); A=ROOT/'artifacts/lab8'
doc=Document(ROOT.parent/'СПЗ 8.docx')
ref=Document(ROOT.parent/'СПЗ 7.docx')
protos={k:deepcopy(ref._element.body[i]) for k,i in {'body':31,'heading':32,'sub':37,'caption':34,'title':29,'conclusion':95}.items()}
for el in list(doc._element.body)[29:]:
 if el.tag!=qn('w:sectPr'): doc._element.body.remove(el)
# The template supplies its original cover, styles, headers, footers and A4 margins.
def para(text, kind='body', page=False):
 p=doc.add_paragraph()
 proto=protos[kind]
 if proto.pPr is not None: p._p.insert(0,deepcopy(proto.pPr))
 if page: p.paragraph_format.page_break_before=True
 if kind in ['heading','sub','title','conclusion']:
  p.paragraph_format.keep_with_next=True
 r=p.add_run(text)
 r.font.name='Times New Roman'; r.font.size=Pt(14)
 r._element.get_or_add_rPr().rFonts.set(qn('w:cs'),'Times New Roman')
 r.font.color.rgb=__import__('docx').shared.RGBColor(0,0,0)
 r.bold=kind in ['heading','title','conclusion']
 return p
num=0
def table(headers, rows, caption, widths=None):
 global num
 num+=1
 t=doc.add_table(rows=1, cols=len(headers)); t.style='Table Grid'
 t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
 usable=16.94
 widths=widths or [usable/len(headers)]*len(headers)
 for col,w in zip(t.columns,widths): col.width=Cm(w)
 for rowi,vals in enumerate([headers]+rows):
  cells=t.rows[0].cells if rowi==0 else t.add_row().cells
  trPr=cells[0]._tc.getparent().get_or_add_trPr()
  trPr.append(OxmlElement('w:cantSplit'))
  if rowi==0: trPr.append(OxmlElement('w:tblHeader'))
  for cell,val,w in zip(cells,vals,widths):
   cell.width=Cm(w); cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   p=cell.paragraphs[0]
   p.paragraph_format.line_spacing=1.5
   p.paragraph_format.space_before=Pt(0); p.paragraph_format.space_after=Pt(0)
   p.paragraph_format.widow_control=True
   if rowi==0: p.alignment=WD_ALIGN_PARAGRAPH.CENTER
   r=p.add_run(str(val)); r.font.name='Times New Roman'; r.font.size=Pt(14); r.bold=rowi==0
   r._element.get_or_add_rPr().rFonts.set(qn('w:cs'),'Times New Roman')
 para(f'Таблиця {num} — {caption}','caption')
 return t

def output(lines):
 # Keep real tool output as selectable text, using the report's typeface.
 for line in lines.splitlines():
  p=para(line)
  p.paragraph_format.first_line_indent=Cm(0)
  p.paragraph_format.line_spacing=1
  p.paragraph_format.keep_with_next=True
 if doc.paragraphs: doc.paragraphs[-1].paragraph_format.keep_with_next=False

para('Реінженерія legacy-модуля: від аналізу до рефакторингу','title',True)
para('Мета роботи','conclusion')
para('Навчитись проводити реінженерію legacy-модуля: аналізувати технічний борг, самостійно виявляти антипатерни, складати план перетворення до реалізації та перевіряти результат вимірюваними метриками й регресійними тестами. Об’єкт роботи за варіантом 2 — модуль обробки замовлень src/process.py проєкту legacy_project_СПЗ_v2.')
para('Крок 1 — Inventory Analysis: збір метрик','heading')
para('1.1 Умови та команди вимірювання','sub')
para('Стан «до» зафіксовано 09.11.2026 до змін process.py. Вихідна точка — коміт 40453d0; у робочому дереві вже є зміни notify.py та його тестів з попередньої роботи. Їх не включено до комітів реінженерії. Середовище вимірювання: Python 3.12.3, pylint 4.1.3, radon 6.0.1, pytest 9.2.0, pytest-cov 7.1.0.')
output('python3 -m pylint src/process.py --score=y\npython3 -m radon cc src/process.py -s\npython3 -m pytest tests/ --cov=src\n    --cov-config=artifacts/lab8/coverage.ini\n    --cov-report=term-missing\nwc -l src/process.py')
para('coverage.ini обмежує звіт файлом src/process.py. Джерело src дозволяє показати 0% навіть тоді, коли модуль не імпортовано жодним тестом. До додавання tests/test_process.py наявний набір містить 14 тестів; усі проходять, але process.py не виконують. Наведені в методичці 12% покриття не відтворилися на фактичному проєкті, тому використано виміряне значення 0%.')
para('1.2 Baseline Metrics та порівняння після змін','sub')
table(['Метрика','До','Після','Δ'],[
 ['pylint score','8.28/10','10.00/10','+1.72'],
 ['Найбільша CC','21: proc','5: _process_order','−16'],
 ['CC: proc','21','3','−18'],
 ['CC: validate_order','8','4','−4'],
 ['LOC усього файлу','177','137','−40'],
 ['Функцій у файлі','4','10','+6'],
 ['Помилки E','0','0','0'],
 ['Попередження W','6','0','−6'],
 ['Test Coverage','0%','100%','+100 в. п.'],
 ['Тестів, що проходять','14','87','+73'],
], 'Метрики process.py до та після реінженерії',[6.1,3.5,3.7,3.64])
para('LOC — фізичні рядки, включно з коментарями й порожніми рядками; кількість функцій не включає два Enum-класи. Покриття — statement coverage цільового модуля. У фінальній версії 82 виконувані оператори, пропусків немає; 100% покриття саме по собі не доводить коректності всіх можливих входів.')
para('1.3 Dependency Map','sub')
table(['Напрям','Залежність та призначення'],[
 ['process.py → src.db','get_data(): читає orders/users/products; save(): записує processed_orders і summary.'],
 ['process.py → src.utils','До: calc, chk, chk2, fmt, format_date, tot, p. Реально потрібні calc та format_date; зайві імпорти прибрано.'],
 ['src.main → process.py','Імпорт proc у рядку 6; run(t=4, d) викликає proc(d), рядок 57.'],
 ['src.analytics → process.py','Локальний імпорт proc у generate_dashboard(), рядок 194; виклик proc(), рядок 205.'],
 ['Тести → process.py','До: прямих тестів немає. Після: tests/test_process.py, 73 тестові випадки.'],
 ['Нові залежності','collections.Counter, enum.Enum/IntEnum — стандартна бібліотека; зовнішніх production-пакетів не додано.'],
], 'Карта залежностей модуля',[5.0,11.94])
para('Пошук виконано через rg -n "process|proc\\(" src tests config та аналіз імпортів. Сигнатуру proc(params=None) збережено для обох споживачів; params і раніше не впливав на результат.')

para('Крок 2 — Antipattern Discovery','heading',True)
para('2.1 Перелік функцій початкового модуля','sub')
table(['Функція / рядки','Поточна відповідальність','LOC','CC'],[
 ['proc\n9–137','Читання даних, пошук зв’язків, обробка статусів, фінанси, форматування, підсумки, запис.','129','21'],
 ['validate_order\n140–156','Перша помилка валідації або (True, None).','17','8'],
 ['calculate_tax\n159–164','Округлений податок: premium або стандартний.','6','2'],
 ['get_discount\n167–175','Знижка premium за двома строгими порогами суми.','9','4'],
], 'Функції process.py до змін',[4.5,9.0,1.72,1.72])
para('2.2 Виявлені антипатерни — рівно 4','sub')
table(['№ / антипатерн','Де у початковому коді','Чому це проблема'],[
 ['1. God Function / змішані відповідальності','proc(), рядки 9–137','129 рядків і CC=21: одна зміна фінансів зачіпає пошук, підсумки та I/O. Окрему бізнес-операцію важко перевірити ізольовано.'],
 ['2. Copy-paste фінансової обробки','Рядки 45–97; calculate_tax/get_discount, 159–175','Три схожі гілки повторюють запис результату й обчислення; окремі helpers дублюють ті самі правила. Зміна ставки може дати різні результати.'],
 ['3. Magic Numbers / Strings','44–52, 66–68, 99, 109, 154, 161–174','Ролі 2/3, ставки 0.15/0.2, пороги 500/1000, знижки 0.03/0.05 і статуси розкидано по умовах; назва політики та єдине місце зміни відсутні.'],
 ['4. Повторний лінійний пошук','Цикл orders, 20; пошук users, 22–26; products, 33–37','Для O замовлень і довідників U/P витрати O(O·(U+P)). Ті самі записи переглядаються багато разів. Індекси дають O(O+U+P) у середньому.'],
], 'Чотири антипатерни та їхні наслідки',[5.0,4.5,7.44])
para('2.3 Тригери реінженерії','sub')
table(['Тригер','Доказ','Присутній / критичність'],[
 ['CC > 15','radon: proc = 21.','Так / висока'],
 ['CFR > 30%','Статистики змін за 3 місяці немає.','Не встановлено'],
 ['God Function','129 рядків; понад 5 відповідальностей, хоча поріг 150 рядків не перевищено.','Так за SRP / висока'],
 ['Code Duplication','Три фінансові гілки та повторні helpers.','Так / висока'],
 ['Mixed Layers','get_data + розрахунки + format_date + save всередині proc.','Так / середня'],
 ['Security Issues','У process.py немає SQL або credentials; борг db.py лежить поза scope.','Ні в модулі'],
 ['Test Debt','До змін: 0% coverage, жодного прямого тесту.','Так / висока'],
], 'Підтверджені тригери реінженерії',[4.4,8.2,4.34])
para('2.4 Обґрунтування реінженерії','sub')
para('Реінженерія виправдана: CC=21 перевищує поріг обов’язкового розгляду, а відсутність тестового покриття поєднується з дублюванням і змішаними відповідальностями. Окрема локальна правка не усуває ці пов’язані причини: потрібна послідовна декомпозиція модуля зі збереженням його зовнішнього контракту. Невідомий CFR не використовується як доказ.')

para('Крок 3 — Reengineering Plan','heading',True)
para('План збережено у artifacts/lab8/REENGINEERING_PLAN.md до редагування продуктового коду. Коміт 1708602 містить план, незмінений baseline-модуль і characterization-тести. Лише наступні коміти змінюють process.py.')
para('3.1 To-Be Architecture','sub')
table(['Функція / компонент','Одна відповідальність','Ціль CC'],[
 ['proc','Координація читання → обробка → запис.','< 8'],
 ['_index_by_id','Індекс із збереженням першого повторного id.','≤ 3'],
 ['_process_order','Перевірка зв’язків і вибір обробника статусу.','≤ 5'],
 ['_order_record','Формування спільних полів результату.','≤ 2'],
 ['_paid_order','Обробка одного оплаченого замовлення.','1'],
 ['_summarize','Лічильники, округлені суми та список помилок.','< 10'],
 ['calculate_tax','Єдина точка розрахунку податку.','< 6'],
 ['get_discount','Єдина точка вибору знижки.','< 6'],
 ['_validation_checks','Лінива послідовність перевірок.','< 6'],
 ['validate_order','Повернення першої помилки валідації.','< 6'],
 ['Role / OrderStatus, константи','Іменовані ролі, статуси, ставки й пороги.','1 для Enum'],
], 'Запланована архітектура process.py',[5.0,9.0,2.94])
para('3.2 Послідовність перетворень','sub')
table(['Ітер.','Техніка та конкретна дія','Критерій Done'],[
 ['1','Characterization tests: усі ролі, межі знижок, статуси, помилки зв’язків, дублікати id, записи save, валідація.','Нові тести проходять на незміненому process.py; усі попередні тести зелені.'],
 ['2','Consolidate Duplicates / Extract Function: одна paid-обробка через calculate_tax/get_discount; виділення підсумків.','Немає трьох копій фінансів; proc CC нижча за 21; повний pytest зелений.'],
 ['3','Indexed lookup / Separate Concerns / Replace Magic Number: індекси, Enum, константи, короткий proc та ліниві перевірки.','proc < 8, validate_order < 6, усі функції < 10; pylint > 7.5, coverage > 80%; pytest зелений.'],
], 'План трьох послідовних ітерацій',[1.3,9.0,6.64])
para('3.3 Reengineering Plan Summary','sub')
table(['Параметр','Значення'],[
 ['Git-гілка','reengineering/process-module; створена від 40453d0.'],
 ['Scope','src/process.py, tests/test_process.py, artifacts/lab8/*, звіт СПЗ 8.docx.'],
 ['Основні техніки','Extract Function, Consolidate Duplicates, Replace Magic Number; індексація довідників.'],
 ['Зовнішній інтерфейс зміниться?','Ні: збережено чотири публічні функції, сигнатури, поля результату, округлення, порядок помилок і два виклики save.'],
 ['Сумісність поведінки','Перший повторний id перемагає; params ігнорується; refunded валідний для validate_order, але невідомий для proc — як у baseline.'],
 ['Відкат','git revert комітів реалізації у зворотному порядку: спочатку 7aff32f, потім a8ada72. План і тести можна залишити.'],
 ['Критерій Done','pylint > 7.5; proc CC < 8; validate_order CC < 6; max CC < 10; coverage > 80%; regression зелений.'],
 ['Очікуваний час','S, близько 4 годин для навчальної роботи.'],
], 'Підсумок плану та обмеження сумісності',[5.0,11.94])
para('Підключення validate_order до proc не планується: це змінило б обробку неповних даних і порядок помилок. Індексація розрахована на штатні hashable ID (цілі числа); некоректні довідники з невалідними записами не входять до контракту цієї роботи.')

para('Крок 4 — Transformation','heading',True)
para('4.1 Підготовка та baseline','sub')
output('git switch -c reengineering/process-module\npython3 -m pytest tests/ -v\n14 passed\npython3 -m radon cc src/process.py -s\nproc: 21; validate_order: 8\npylint: 8.28/10; LOC: 177; coverage: 0%')
para('Вихідний текст збережено як artifacts/lab8/process_before.py. Наявні зміни попередньої лабораторної залишено в робочому дереві й не включено до локальних комітів №8.')
para('4.2 Результати кожної ітерації','sub')
table(['Іт.','Що зроблено','Тести','CC proc','Коміт'],[
 ['1','73 нові characterization-випадки; план і baseline.','87 ✓','21 → 21','1708602\ntest(process)'],
 ['2','Спільна paid-обробка та підсумки; виклик фінансових helpers.','87 ✓','21 → 11','a8ada72\nrefactor(process)'],
 ['3','Індекси, окрема обробка замовлення, Enum і константи, лінива валідація.','87 ✓','11 → 3','7aff32f\nrefactor(process)'],
], 'Фактичні результати трьох ітерацій',[0.8,7.0,2.2,2.4,4.54])
para('Після другої ітерації покриття вже становило 100%, але proc із CC=11 ще не відповідав цілі. Третя ітерація завершила структурне розділення: proc має 17 рядків, валідація — 6; максимальна CC=5 у _process_order. LOC усього файлу залишився 137, що відповідає дозволеній альтернативі «розбитий на функції».')
para('4.3 Історія локальних комітів','sub')
for line in (A/'git_log.txt').read_text().splitlines()[:3]:
 hash_,message=line.split(' ',1)
 output(hash_+'\n'+message)
para('Наведено фактичний git log --oneline для трьох завершених ітерацій. Коміти локальні; для кожного кроку збережено вивід тестів і статичного аналізу.')
para('4.4 Зміст фінальної реалізації','sub')
table(['Елемент','Результат'],[
 ['Довідники','Один прохід users/products і setdefault(id, item): перший дублікат збережено, повторні пошуки прибрано.'],
 ['Фінанси','calculate_tax та get_discount — єдине місце ставок і знижок; _paid_order формує фінансові поля. calc зберігає round(..., 2).'],
 ['Статуси','Role/OrderStatus замість magic values; Enum узгоджені з початковими int/str. У результаті залишаються рядкові статуси.'],
 ['Підсумки','Counter та суми по сформованих записах; I/O зосереджено в proc.'],
 ['Валідація','Лінивий генератор зупиняється на першій помилці; збережено порядок перевірок, допуск NaN та початковий TypeError для None/рядкової суми.'],
], 'Основні рішення реалізації',[4.2,12.74])

para('Крок 5 — Verification','heading',True)
para('5.1 Metrics Comparison','sub')
para('Повна таблиця before/after наведена у Кроці 1 (Таблиця 1). Підсумок: pylint 8.28 → 10.00, CC proc 21 → 3, CC validate_order 8 → 4, максимальна CC 21 → 5, LOC 177 → 137, coverage 0 → 100%, тести 14 → 87. Усі метрики знято тим самим набором інструментів.')
para('5.2 Three-Check Verification','sub')
table(['Перевірка','Команда / дія','Результат','Статус'],[
 ['Функціональність збережена?','pytest tests/ -v','87 passed; усі 14 baseline-тестів збережено.','✓'],
 ['pylint покращився?','pylint src/process.py --score=y','10.00/10, було 8.28; E=0, W=0.','✓'],
 ['CC нижча за 10?','radon cc src/process.py -s','max=5; proc=3; validate_order=4.','✓'],
 ['Покриття > 80%?','pytest --cov=src; фільтр process.py','82 statements, 0 missed, 100%.','✓'],
 ['Поведінка baseline збігається?','check_compatibility.py; seed=8','200 пакетів і demo-дані: однакові результати та save.','✓'],
], 'Перевірка результатів реінженерії',[4.3,6.0,5.4,1.24])
para('Фрагмент фактичного виводу інструментів:')
output('Name                 Stmts   Miss  Cover\nsrc/process.py          82      0   100%\n87 passed\nYour code has been rated at 10.00/10\nF 61:0 _process_order - A (5)\nF 116:0 validate_order - A (4)\nF 34:0 proc - A (3)')
para('Додаткова перевірка порівнює фінальний модуль із збереженим baseline на 200 детермінованих пакетах (seed=8): різні ролі, статуси, пороги, відсутні зв’язки та повторні id. Звіряються і результат, і обидва записи save. На вбудованих demo-даних обидві версії повертають processed=2, pending=1, cancelled=1, total_revenue=1385.00, total_tax=255.00.')
para('5.3 Трасування вимог варіанта 2 на перевірки','sub')
table(['Обов’язкова вимога','Чим підтверджено'],[
 ['proc — оркестратор, CC < 8','radon: 3; лише читання, цикл координації, підсумки й запис.'],
 ['Одна логіка податків / знижок','_paid_order → calculate_tax/get_discount; повторні фінансові гілки видалено.'],
 ['Іменовані значення','Role, OrderStatus, STANDARD/PREMIUM_TAX_RATE, PREMIUM_DISCOUNT_TIERS, VALID_STATUSES.'],
 ['Параметризовані premium / regular / other','test_paid_roles_and_discount_boundaries: 6 ролей × 6 сум = 36 випадків.'],
 ['Граничні випадки validate_order','19 параметрів: порожні дані, відсутні поля, сума −0.01/0/0.01, статуси й порядок помилок; ще 2 перевірки TypeError.'],
 ['Поведінка збережена','Тести результатів, двох save, незмінності входів, дублікатів, дат і refunded; 200 differential-порівнянь.'],
], 'Зв’язок вимог із тестами та метриками',[6.0,10.94])
para('5.4 Code Review Checklist','sub')
table(['Критерій','Так','Ні'],[
 ['Кожна нова функція має одну відповідальність (SRP).','✓',''],
 ['Усі 4 антипатерни з Кроку 2 усунено.','✓',''],
 ['Дублювання фінансової обробки видалено.','✓',''],
 ['Усі нові функції мають docstring.','✓',''],
 ['Нові функції виконуються регресійними тестами.','✓',''],
 ['git log містить коректні повідомлення комітів.','✓',''],
 ['Публічні сигнатури та результат не порушено.','✓',''],
 ['У process.py немає credentials; ставки й пороги іменовані.','✓',''],
], 'Підсумкова перевірка коду',[13.94,1.5,1.5])
para('Розділення відповідальностей перевірено читанням фінального коду; покриття та git log доповнюють цю перевірку. Наявні credentials у db.py не належать до process.py й не усувалися у межах цього варіанта.')

para('Крок 6 — Lessons Learned','heading',True)
table(['Поле','Результат'],[
 ['Скільки ітерацій виконано?','3: спочатку characterization-тести, потім об’єднання фінансів, далі індекси та завершення декомпозиції.'],
 ['Найважча ітерація і чому','Третя: індекс не повинен міняти вибір першого дубліката, а спрощення validate_order — порядок помилок. Для цього використано setdefault та ліниві перевірки.'],
 ['Чи виникала регресія?','Ні: після кожної ітерації 87 passed. На baseline до нових тестів — 14 passed. Порівняння 200 пакетів і demo-даних теж пройшло.'],
 ['Lesson learned #1','Високий початковий pylint (8.28) не означає просту архітектуру: proc усе ще мав CC=21 і 129 рядків. Потрібна сукупність метрик та аналіз відповідальностей.'],
 ['Lesson learned #2','Поведінка включає дрібні історичні правила: >500 і >1000, перший id, refunded та першу помилку. Тести до змін дозволили зберегти їх без припущень.'],
 ['Що змінити в наступному плані?','Відразу включати автоматичне збереження метрик і перевірку імпортованості модуля: відсутність coverage-даних не треба плутати з 0% покриття. Окремо планувати майбутнє узгодження refunded.'],
 ['Чи досягнуто Done?','Так: pylint=10.00 > 7.5; proc CC=3 < 8; validate_order CC=4 < 6; max CC=5 < 10; coverage=100% > 80%; усі тести зелені.'],
], 'Lessons Learned і завершення роботи',[5.2,11.74])
para('Висновок','conclusion')
para('У роботі виконано реінженерію process.py за варіантом 2: зібрано baseline, самостійно визначено рівно чотири антипатерни, зафіксовано план до змін, виконано три ітерації та перевірено результат. proc перетворено на координатор; фінансові правила зведено до одного місця, повторні пошуки замінено індексами, ролі, статуси й числові політики отримали імена.')
para('Складність proc зменшилася з 21 до 3, validate_order — з 8 до 4; pylint зріс із 8.28 до 10.00, а покриття — з 0 до 100%. Усі 87 тестів проходять; порівняння з baseline підтвердило сумісність результатів і записів. Отже, усі критерії варіанта 2 досягнуто без зміни публічного контракту модуля.')
para('Артефакти роботи','sub')
para('src/process.py — реалізація; tests/test_process.py — 73 тестові випадки; artifacts/lab8/REENGINEERING_PLAN.md — план; before/, iteration1/, iteration2/, after/ — сирі результати інструментів; process_before.py — вихідний код; compatibility.txt і check_compatibility.py — перевірка сумісності; git_log.txt — історія комітів. Для відтворення метрик використовується measure.py; версії пакетів наведено в tool_versions.txt.')
# Clear unrelated document metadata left by the source report.
doc.core_properties.title='Практичне заняття №8. Реінженерія process.py. Варіант 2'
doc.core_properties.subject='Супроводження програмного забезпечення'
doc.core_properties.author='Будова Д. О.'
doc.core_properties.comments=''
for rid, rel in list(doc.part.rels.items()):
 if rel.reltype.endswith('/image'):
  doc.part.drop_rel(rid)
out=A/'СПЗ 8.docx'; doc.save(out)
print(out)
print('Tables:',num)
