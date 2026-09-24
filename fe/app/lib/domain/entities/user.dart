class User {
  final String username;
  final String phone;
  final String address;
  final String password;

  const User({
    required this.username,
    required this.phone,
    required this.address,
    required this.password,
  });

  Map<String, dynamic> toJson() => {
        'username': username,
        'phone': phone,
        'address': address,
        'password': password,
      };

  factory User.fromJson(Map<String, dynamic> json) => User(
        username: json['username'] as String? ?? '',
        phone: json['phone'] as String? ?? '',
        address: json['address'] as String? ?? '',
        password: json['password'] as String? ?? '',
      );

  User copyWith({
    String? username,
    String? phone,
    String? address,
    String? password,
  }) =>
      User(
        username: username ?? this.username,
        phone: phone ?? this.phone,
        address: address ?? this.address,
        password: password ?? this.password,
      );
}
