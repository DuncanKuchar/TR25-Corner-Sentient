% disp(x.Properties.VariableNames)
x=readtable("data/test 6/logfiles/rc_14.log");
lat=x.Latitude__Degrees___180_0_180_0_10;
long=x.Longitude__Degrees___180_0_180_0_10;
Speed=x.Speed__kph__0_0_150_0_10/3600;
% Power=Accelx*650/32.2*2/3/1.667/2.11/2.75;
ay = abs(x.AccelY__G___3_0_3_0_25);
ax = x.AccelX__G___3_0_3_0_25;
RPM = x.RPM____0_10000_25;
CoolantTemp = x.EngineTemp__C__0_200_1;
TPS = x.TPS_____0_0_100_0_25; % Import TPS using the correct name
brakepress = x.FrontBP__psi___5_0_5_0_25; % Import FrontBP as brakepress using the correct name
accel_x = ax;
accel_y = ay;
steering_angle = x.SteerAng__Degrees___145_145_25; % Import steering angle
speed = x.Speed__kph__0_0_150_0_10; % Import speed in kph
currentstate = 0;
nextstate = 0;
lpd = 1; % Process every line (data point)
statehistory = zeros(length(lat),1); % Initialize state history for all data points
for i = 1:length(lat) % Iterate through all data points
   currIndex = i; % The current index in state history is simply the loop index
   switch (currentstate)
        case 1
            if (((brakepress(i) > 30) ...
                    || (accel_x(i) > 0.3)) ...
                || ((steering_angle(i) > 40) ...
                    || (abs(accel_y(i)) > 1.1)))
                nextstate = 0;
            elseif ((abs(accel_y(i)) < 0.7) ...
                    && ((steering_angle(i) < 20)) && (TPS(i) > 15))
                nextstate = 2;
            end
        case 2
            if ((TPS(i) < 50) ... % This condition being lower causes the wings to open earlier at low speed high Gs
                || (steering_angle(i) > 40) ... % Changed from && to || ?
                        || (abs(accel_y(i)) > 1.1)) ... % New
                    || ((brakepress(i) > 30) ...
                        || (accel_x(i) > 0.3))
                nextstate = 0;
            elseif ((speed(i) > 15) ...
                    && (accel_y(i) > 0.7) ...
                        || (steering_angle(i) > 20)) % This condition may be danger if we can't rely on steer angle
                nextstate = 1;
            end
        otherwise
            if ((TPS(i) > 50) ...
                && (steering_angle(i) < 30) ...
                && (accel_y(i) < 0.7) ...
                && (brakepress(i) < 30))
                nextstate = 2;
            elseif ((speed(i) > 15) ...
                    && (accel_y(i) < 1.1) ...
                    && (steering_angle(i) < 30)) ... % Changed from || to &&
                && ((brakepress(i) < 50) && (accel_x(i) < 0.4)) % Both New
                nextstate = 1;
            end
   end
   currentstate = nextstate;
   statehistory(currIndex) = currentstate;
end
colormap(cool)
scatter3(ax, ay, Speed*3600,[],statehistory,'filled') % Use all data for scatter plot
c = colorbar;
c.Label.String = "FSM State";
clim([-0.25 2.1]);
title("X/Y Acceleration vs Speed (Indicating FSM State)")
xlabel("X Acceleration (positive = car decelerating)")
ylabel("Y Acceleration")
zlabel("Speed (kph)")
xlim([-1.5 1.5])
ylim([-1.5 1.5])
zlim([0 150])
scatterSize = 20; % Define a constant scatter size
figure;
t = tiledlayout(3,2, 'Padding', 'compact', 'TileSpacing', 'compact'); % Increased rows to accommodate the new plot
% 1. Lateral Acceleration
nexttile;
geoscatter(lat, long, scatterSize, ay, 'filled');
geobasemap('satellite');
colorbar;
title('Lateral Acceleration (G)');
% 2. Longitudinal Acceleration
nexttile;
geoscatter(lat, long, scatterSize, ax, 'filled');
geobasemap('satellite');
colorbar;
title('Longitudinal Acceleration (G)');
% 3. Engine RPM
nexttile;
geoscatter(lat, long, scatterSize, RPM, 'filled');
geobasemap('satellite');
colorbar;
title('Engine RPM');
% 4. Coolant Temperature
nexttile;
geoscatter(lat, long, scatterSize, CoolantTemp, 'filled');
geobasemap('satellite');
colorbar;
title('Coolant Temperature (°C)');
% 5. GPS and FSM State
%colormap(cool)
nexttile;
geoscatter(lat, long, scatterSize, statehistory, 'filled');
geobasemap('satellite');
c_gps = colorbar;
c_gps.Label.String = "FSM State";
clim([-0.25 2.1]);
title('GPS Location Colored by FSM State');