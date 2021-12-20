class KalmanRSSI:
    def __init__(self, R=1, Q=1, A=1, B=0, C=1) -> None:
        self.R = R  # noise power desirable
        self.Q = Q  # noise power estimated

        self.A = A
        self.C = C
        self.B = B
        self.cov = None
        self.x = None

    def filter(self, z, u=0):
        if self.x is None:
            self.reset(z)
        else:
            # Compute prediction
            predX = self.predict(u)
            predCov = self.uncertainty()

            # Kalman gain
            K = predCov * self.C * (1 / ((self.C * predCov * self.C) + self.Q))

            # Correction
            self.x = predX + K * (z - (self.C * predX))
            self.cov = predCov - (K * self.C * predCov)

        return self.x

    def reset(self, z):
        self.x = (1 / self.C) * z
        self.cov = (1 / self.C) * self.Q * (1 / self.C)
        return self.x

    def predict(self, u=0):
        return (self.A * self.x) + (self.B * u)

    def uncertainty(self):
        return ((self.A * self.cov) * self.A) + self.R

    def lastMeasurement(self):
        return self.x

    def setMeasurementNoise(self, noise):
        self.Q = noise

    def setProcessNoise(self, noise):
        self.R = noise
