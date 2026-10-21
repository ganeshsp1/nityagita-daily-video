import 'dart:math';
void main(List<String> a) {
  final d = DateTime.parse(a[0]);
  print(Random(int.parse('${d.year}${d.month}${d.day}')).nextInt(658) + 1);
}
