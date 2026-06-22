clear; clc; close all;

%% =========================
%  基本設定
% =========================
filename = 'Fresnel_data.xlsx';
sheetName = 'Sheet1';

n1 = 1.48;        % 入射介質：空氣
n2 = 1.0;       % 折射介質折射率

% 若你的反射角是用「同側正角度」記錄，設 +1
% 若你的反射角是用「反射到另一側所以變負」記錄，設 -1
reflectionSign = +1;

%% =========================
%  讀取 Excel
%  假設五欄依序為：
%  theta_i, theta_r, theta_t, I_r, I_t
% =========================
data = readmatrix(filename, 'Sheet', sheetName, 'Range', 'M19:Q29');

theta_i_all = data(:,1);   % 入射角 degree
theta_r_all = data(:,2);   % 反射角 degree
theta_t_all = data(:,3);   % 折射角 degree
I_r_all     = data(:,4);   % 反射強度
I_t_all     = data(:,5);   % 折射強度

%% =========================
%  分別建立有效資料
%  不要把所有欄位一起 valid
% =========================

% 反射角資料
valid_theta_r = ~isnan(theta_i_all) & ~isnan(theta_r_all);
theta_i_r = theta_i_all(valid_theta_r);
theta_r   = theta_r_all(valid_theta_r);

% 折射角資料
valid_theta_t = ~isnan(theta_i_all) & ~isnan(theta_t_all);
theta_i_t = theta_i_all(valid_theta_t);
theta_t   = theta_t_all(valid_theta_t);

% 反射強度資料
valid_Ir = ~isnan(theta_i_all) & ~isnan(I_r_all);
theta_i_Ir = theta_i_all(valid_Ir);
I_r = I_r_all(valid_Ir);

% 折射強度資料
valid_It = ~isnan(theta_i_all) & ~isnan(I_t_all);
theta_i_It = theta_i_all(valid_It);
I_t = I_t_all(valid_It);

%% =========================
%  Figure 1: 驗證反射定律
% =========================
theta_r_theory = reflectionSign * theta_i_r;

figure;

scatter(theta_i_r, theta_r, 70, 'filled');
hold on;

plot(theta_i_r, theta_r_theory, 'LineWidth', 2);

grid on;
xlabel('\theta_i (degree)');
ylabel('\theta_r (degree)');
title('Reflection Law Verification');

legend('Measured \theta_r', ...
       'Theory: \theta_r = \theta_i', ...
       'Location', 'best');

saveas(gcf, 'reflection_law_TE_TM_average.png');

%% =========================
%  Figure 2: 驗證 Snell law
% =========================
theta_t_theory = asind((n1/n2) .* sind(theta_i_t));

figure;

scatter(theta_i_t, theta_t, 70, 'filled');
hold on;

plot(theta_i_t, theta_t_theory, 'LineWidth', 2);

grid on;
xlabel('\theta_i (degree)');
ylabel('\theta_t (degree)');
title('Snell Law Verification');

legend('Measured \theta_t', ...
       'Theory: n_1 sin\theta_i = n_2 sin\theta_t', ...
       'Location', 'best');

saveas(gcf, 'snell_law_TE_TM_average.png');

%% =========================
%  Figure 3: (TE + TM) / 2 Fresnel 反射率與穿透率
% =========================
% R = I_r / (I_r + I_t)
% T = I_t / (I_r + I_t)
%
% 注意：
% 必須同一個入射角同時有 I_r 和 I_t，才能計算 R 和 T
% 所以這裡只使用共同角度

[theta_common, idx_Ir, idx_It] = intersect(theta_i_Ir, theta_i_It, 'stable');

Ir_common = I_r(idx_Ir);
It_common = I_t(idx_It);

I_total = Ir_common + It_common;

R_exp = Ir_common ./ I_total;
T_exp = It_common ./ I_total;

%% =========================
%  建立 Fresnel 理論曲線
% =========================
theta_all_valid = theta_i_all(~isnan(theta_i_all));

theta_plot = linspace(min(theta_all_valid), max(theta_all_valid), 1000);

sin_theta_t_plot = (n1/n2) .* sind(theta_plot);

% 判斷是否有實數折射角
not_TIR = abs(sin_theta_t_plot) <= 1;

R_avg = zeros(size(theta_plot));
T_avg = zeros(size(theta_plot));

theta_valid = theta_plot(not_TIR);
theta_t_plot = asind((n1/n2) .* sind(theta_valid));

ci = cosd(theta_valid);
ct = cosd(theta_t_plot);

%% =========================
%  TE mode Fresnel equations
%  又稱 s-polarization
% =========================

% TE reflection coefficient
r_TE = (n1 .* ci - n2 .* ct) ./ ...
       (n1 .* ci + n2 .* ct);

% TE transmission coefficient
t_TE = (2 .* n1 .* ci) ./ ...
       (n1 .* ci + n2 .* ct);

R_TE = abs(r_TE).^2;

T_TE = (n2 .* ct) ./ (n1 .* ci) .* abs(t_TE).^2;

%% =========================
%  TM mode Fresnel equations
%  又稱 p-polarization
% =========================

% TM reflection coefficient
r_TM = (n2 .* ci - n1 .* ct) ./ ...
       (n2 .* ci + n1 .* ct);

% TM transmission coefficient
t_TM = (2 .* n1 .* ci) ./ ...
       (n2 .* ci + n1 .* ct);

R_TM = abs(r_TM).^2;

T_TM = (n2 .* ct) ./ (n1 .* ci) .* abs(t_TM).^2;

%% =========================
%  TE 和 TM 平均
% =========================
R_avg(not_TIR) = (R_TE + R_TM) ./ 2;
T_avg(not_TIR) = (T_TE + T_TM) ./ 2;

% 若發生全反射，理論上 R = 1, T = 0
R_avg(~not_TIR) = 1;
T_avg(~not_TIR) = 0;

% 避免 NaN 或 Inf
bad_R = ~isfinite(R_avg);
bad_T = ~isfinite(T_avg);

R_avg(bad_R) = 1;
T_avg(bad_T) = 0;

%% =========================
%  Plot 反射率與穿透率
% =========================
figure;

scatter(theta_common, R_exp, 70, 'filled');
hold on;

scatter(theta_common, T_exp, 70, 'filled');

plot(theta_plot, R_avg, 'LineWidth', 2);
plot(theta_plot, T_avg, 'LineWidth', 2);

grid on;
xlabel('\theta_i (degree)');
ylabel('Reflectance / Transmittance');
title('(TE + TM) / 2 Fresnel Reflectance and Transmittance');

legend('Measured R = I_r / (I_r + I_t)', ...
       'Measured T = I_t / (I_r + I_t)', ...
       '(TE + TM)/2 Fresnel R theory', ...
       '(TE + TM)/2 Fresnel T theory', ...
       'Location', 'best');

ylim([0 1.1]);

saveas(gcf, 'TE_TM_average_fresnel_RT.png');

%% =========================
%  Figure 4: 原始反射與折射強度
%  這張圖會把所有 I_r 和 I_t 資料點都畫出來
% =========================
figure;

scatter(theta_i_Ir, I_r, 70, 'filled');
hold on;

scatter(theta_i_It, I_t, 70, 'filled');

grid on;
xlabel('\theta_i (degree)');
ylabel('Measured Intensity');
title('Measured Reflected and Transmitted Intensities');

legend('Measured I_r', ...
       'Measured I_t', ...
       'Location', 'best');

saveas(gcf, 'raw_intensity_points_TE_TM_average.png');

%% =========================
%  顯示誤差資訊
% =========================
fprintf("Reflection law RMS error = %.4f degree\n", ...
    rms(theta_r - theta_r_theory));

fprintf("Snell law RMS error = %.4f degree\n", ...
    rms(theta_t - theta_t_theory));

theta_B = atand(n2/n1);

fprintf("TM Brewster angle = %.4f degree\n", theta_B);
fprintf("(TE + TM)/2 mode uses average reflectance and transmittance.\n");

fprintf("Number of reflection angle points = %d\n", length(theta_r));
fprintf("Number of refraction angle points = %d\n", length(theta_t));
fprintf("Number of reflected intensity points = %d\n", length(I_r));
fprintf("Number of transmitted intensity points = %d\n", length(I_t));
fprintf("Number of common intensity points used for R/T = %d\n", length(theta_common));