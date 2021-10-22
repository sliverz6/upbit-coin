import pyupbit

access = "FalkzhtP5xxwmqIm3xnnInSQWelQOR2xml6g48xf"
secret = "Y3nwdG4s0ONwq0KWKsnHBInzW8qoN3kk7cXxkROV"
upbit = pyupbit.Upbit(access, secret)

print(upbit.get_balance("KRW-MED"))     # KRW-XRP 조회
print(upbit.get_balance("KRW"))         # 보유 현금 조회
