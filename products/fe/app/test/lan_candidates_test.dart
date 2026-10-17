import 'package:app/core/platform/lan_candidates_io.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('scans the actual /20 subnet, starting with the phone /24', () {
    final candidates = lanCandidatesForSubnet('10.10.7.44', 20, 8000);

    expect(candidates, hasLength(4093));
    expect(
      candidates.take(253).every((url) => url.startsWith('http://10.10.7.')),
      isTrue,
    );
    expect(candidates, contains('http://10.10.7.158:8000'));
    expect(candidates, contains('http://10.10.0.1:8000'));
    expect(candidates, isNot(contains('http://10.10.7.44:8000')));
  });

  test('rejects public and invalid networks, bounds wider subnets to /24', () {
    expect(lanCandidatesForSubnet('8.8.8.8', 24, 8000), isEmpty);
    expect(lanCandidatesForSubnet('10.10.7.4', 33, 8000), isEmpty);
    expect(lanCandidatesForSubnet('10.10.7.4', 24, 0), isEmpty);

    final candidates = lanCandidatesForSubnet('10.10.7.4', 16, 8000);
    expect(candidates, hasLength(253));
    expect(candidates, everyElement(startsWith('http://10.10.7.')));
    expect(candidates, isNot(contains('http://10.10.8.1:8000')));
  });
}
