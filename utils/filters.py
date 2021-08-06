

class KalmanAngle:
    def __init__(self):
        # Q (ANGLE) unknown uncertainty from the environment
        self.QAngle = 0.001
        # Q (BIAS) unknown uncertainty from the environment. Here - covariance is degree of correlation
        # between variances of the angle and its error/bias.
        self.QBias = 0.003
        self.RMeasure = 0.1
        self.angle = 0.0
        self.bias = 0.0
        self.rate = 0.0
        self.P = [[0.0, 0.0], [0.0, 0.0]]

    def get_angle(self, new_angle, new_rate, dt):
        # step 1: Predict new state (for our case - state is angle) from old state + known external influence
        self.rate = new_rate - self.bias  # new_rate is the latest Gyro measurement
        self.angle += dt * self.rate

        # step 2: Predict new uncertainty (or covariance) from old uncertainity and unknown uncertainty from the environment.
        self.P[0][0] += dt * (dt * self.P[1][1] - self.P[0][1] - self.P[1][0] + self.QAngle)
        self.P[0][1] -= dt * self.P[1][1]
        self.P[1][0] -= dt * self.P[1][1]
        self.P[1][1] += self.QBias * dt

        # step 3: Innovation i.e. predict th next measurement
        y = new_angle - self.angle

        # step 4: Innovation covariance i.e. error in prediction
        s = self.P[0][0] + self.RMeasure

        # step 5:  Calculate Kalman Gain
        k = [0.0, 0.0]
        k[0] = self.P[0][0] / s
        k[1] = self.P[1][0] / s

        # step 6: Update the Angle
        self.angle += k[0] * y
        self.bias += k[1] * y

        # step 7: Calculate estimation error covariance - Update the error covariance
        p00_temp = self.P[0][0]
        p01_temp = self.P[0][1]

        self.P[0][0] -= k[0] * p00_temp
        self.P[0][1] -= k[0] * p01_temp
        self.P[1][0] -= k[1] * p00_temp
        self.P[1][1] -= k[1] * p01_temp
        return self.angle
