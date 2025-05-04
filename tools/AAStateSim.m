%% 
% Graceful degredation checklist:
% 
% (Out of range: too positive = +, too negative = -, zero = ~)
% 
% No steering angle:                                                                                                          
% +/- Only High DF                                                                                                             
% ~ OK
% 
% No brake pressure:                                                                                                         
% + Biases entirely to high DF                                                                                            
% ~/- Mostly OK but the initial Med --> Hi response to braking is slightly slower
% 
% No X Accel:                                                                                                                 
% +/~ OK System biases towards high DF insead of medium                                            
% - OK
% 
% No Y Accel:                                                                                                                     
% ~ BAD. System biases a lot towards using low DF when accelerating. This may 
% be due to bad steering angle data.
% 
% No Speed:                                                                                                                      
% + Car may use medium downforce at low speed                                                         
% ~/- OK Loss of Medium Downforce functionality, but biases towards high DF instead

accel_x = input("X acceleration: ");
accel_y = input("Y acceleration: ");
TPS = input("TPS: ");
speed = input("Front wheel speed: ");
brakepress = input("Brake pressure: ");
steering_angle = input("Steering angle: ");
lpd = input("Lines per data in file: ");
startidx = input("Start index: ");
endidx = input("End index: ");
%% 
% For older miscalibrated data, brake pressure may need to be multiplied by 
% 10.
% 
% Car accelerating forward should be negative x acceleration.

currentstate = 0
nextstate = 0
statehistory = zeros(ceil((endidx-startidx)/lpd),1);

for i = (startidx):lpd:(endidx)
   currIndex = (i + lpd - startidx)/lpd;
   if (i > 1) && (isnan(steering_angle(i)))
       steering_angle(i) = steering_angle(i-lpd);
       speed(i) = speed(i-lpd);
   end

   if (i > 1) && (isnan(accel_x(i)))
       accel_x(i) = accel_x(i-lpd);
       accel_y(i) = accel_y(i-lpd);
       brakepress(i) = brakepress(i-lpd);
       TPS(i) = TPS(i-lpd);
   end


   switch (currentstate)
        case 1
            if (((brakepress(i) > 30) ...
                    || (accel_x(i) > 0.3)) ...
                || ((steering_angle(i) > 40) ...
                    || (abs(accel_y(i)) > 1.1)))
                nextstate = 0;
            elseif ((abs(accel_y(i)) < 0.5) ...
                    && (steering_angle(i) < 20) ...
                    && (TPS(i) > 20)) % New
                nextstate = 2;
            end
        case 2
%% 
% The thresholds from high to low DF need to be slightly more picky to allow 
% medium DF to happen.

            if ((TPS(i) < 20) ... % This condition being lower causes the wings to open earlier at low speed high Gs
                && (((steering_angle(i) > 40) ... % Changed from && to || ?
                        || (abs(accel_y(i)) > 1.1)) ... % New
                    || ((brakepress(i) > 30) ...
                        || (accel_x(i) > 0.3))))
                nextstate = 0;
            elseif ((speed(i) > 15) ...
                    && ((abs(accel_y(i)) > 0.5) ...
                        || (steering_angle(i) > 20))) % This condition may be danger if we can't rely on steer angle
                nextstate = 1;
            end
        otherwise
            if ((TPS(i) > 20) ...
                && (steering_angle(i) < 30) ...
                && (abs(accel_y(i)) < 0.5) ...
                && (brakepress(i) < 30))
%% 
% This parameter determines how readily the system will go from high to low 
% DF. It may impact downshif blipping if the value is set too high.

                nextstate = 2;
            elseif ((speed(i) > 15) ...
%% 
% This condition changes the line at which medium downforce is considered an 
% option:
% 
% 

                && ((abs(accel_y(i)) < 1.1) ...
%% 
% This parameter influences whether the system will choose high or medium downforce 
% when accelerating and traveling above the minimum speed:
% 
% 
% 
% Obviously the choice in steering angle will affect this as well:

                    && (steering_angle(i) < 30)) ... % Changed from || to &&
                && ((brakepress(i) < 50) && (accel_x(i) < 0.4))) % Both New
%% 
% The brake pressure parameter here mostly determines if/when the car will switch 
% to medium wings when coasting. A higher value means more aggressive trail braking 
% is allowed for medium wings:
% 
% 

                nextstate = 1;
            end
   end

   currentstate = nextstate;
   statehistory(currIndex) = currentstate;
end

figure(1)
colormap(cool)
scatter3(accel_x(startidx:lpd:endidx), accel_y(startidx:lpd:endidx),speed(startidx:lpd:endidx),[],statehistory,'filled')
c = colorbar;
c.Label.String = "FSM State";
clim([-0.25 2.1]);
title("X/Y Acceleration vs Speed (FSM State)")
xlabel("X Acceleration (positive = car decelerating)")
ylabel("Y Acceleration")
zlabel("Speed")
xlim([-1.5 1.5])
ylim([-1.5 1.5])
zlim([10 65])

figure(2)
colormap(cool)
scatter((startidx:lpd:endidx),speed(startidx:lpd:endidx),[],statehistory,'filled');
c = colorbar;
c.Label.String = "FSM State";
clim([-0.25 2.1]);
title("Speed vs Time (FSM State)")
xlabel("Time")
ylabel("Speed")
xlim([1500 11500])
ylim([0 70])