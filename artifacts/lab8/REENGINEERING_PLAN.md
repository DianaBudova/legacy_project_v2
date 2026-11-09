# Reengineering Plan — process.py, варіант 2

План зафіксовано 09.11.2026 до редагування src/process.py.
Гілка: reengineering/process-module. Початкова точка: 40453d0.
Робоче дерево вже містить зміни попередньої роботи у notify.py та її тестах;
вони залишаються поза комітами цієї роботи.

## Чотири антипатерни
1. God Function / Mixed Responsibilities — proc(), рядки 9–137: завантаження,
   пошук сутностей, фінансові правила, форматування, агрегація та збереження.
2. Copy-paste — рядки 45–97 та 159–175: три схожі гілки, дублювання податків і знижок.
3. Magic Numbers / Strings — рядки 44–52, 66–68, 99, 109, 154, 161–174:
   числові ролі, ставки, пороги й статуси без іменованої політики.
4. Repeated Linear Search — рядки 20–37: повторний пошук user/product для кожного
   замовлення; O(O*(U+P)) замість O(O+U+P).

## Контракт та архітектура
Публічні proc(params=None), validate_order(o), calculate_tax(amount, role),
get_discount(amount, role) та структура результату залишаються сумісними.
params залишається прийнятим, але невикористаним. calc() зберігає округлення.
validate_order() надалі приймає refunded, а proc() повертає для нього unknown
status: це зафіксована поведінка, а її виправлення потребує окремої зміни.
Не підключати валідацію до proc(): це змінило б порядок/тип існуючих помилок.
При однакових id у довіднику залишити перший запис, як у baseline.

Майбутні відповідальності: proc — I/O та координація (CC < 8);
_index_by_id — індексація першого id (CC <= 3);
_process_order — перевірка зв'язків і вибір обробника (CC <= 5);
_paid_order — фінанси одного paid-замовлення (CC = 1);
_order_record — спільні поля результату (CC = 1);
_summarize — підсумки (CC < 10);
calculate_tax / get_discount — єдине джерело ставок і знижок (CC < 6);
validate_order / _validation_checks — упорядковані перевірки (CC < 6).

## Ітерації та критерії завершення
1. Characterization tests на незміненому модулі: premium/regular/other,
   межі 500/1000, всі статуси, помилки зв'язків, дублікати id,
   порожні дані, side effects save, граничні значення validate_order.
   Done: повний pytest зелений до змін продуктового коду.
2. Consolidate Duplicates + Extract Function: прибрати три фінансові гілки,
   використати calculate_tax/get_discount та спільний запис результату;
   виділити підсумки. Done: regression зелений, CC proc знижується.
3. Replace Magic Numbers + indexed lookup + Separate Concerns:
   Enum/константи, індекси зі збереженням першого id, короткий proc,
   упорядковані правила валідації. Done: proc < 8, validate_order < 6,
   усі функції < 10, pylint > 7.5, coverage > 80%, pytest зелений.

## Scope, відкат і оцінка
src/process.py, tests/test_process.py, artifacts/lab8/* та звіт СПЗ 8.docx.
Основні техніки: Extract Function, Consolidate Duplicates, Replace Magic Number.
Без змін db.py/utils.py/notify.py, нових production-залежностей або міграцій.
Відкат: git revert комітів реінженерії у зворотному порядку; попередні правки
notify.py не включати. Оцінка навчальної роботи: S, близько 4 годин.
Перевірка: pylint, radon, pytest-cov, code review, порівняння before/after.
