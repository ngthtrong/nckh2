import '../entities/rescue_record.dart';
import '../repositories/rescue_repository.dart';

class GetRescueRecordsUseCase {
  final RescueRepository repository;

  GetRescueRecordsUseCase(this.repository);

  List<RescueRecord> call() {
    return repository.getAllRecords();
  }
}
