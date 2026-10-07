`default_nettype none

module spi_peripheral (
    input wire clk,
    input wire rst_n,
    input wire copi,
    input wire ncs,
    input wire sclk,

    output reg [7:0]  en_reg_out_7_0,
    output reg [15:8] en_reg_out_15_8,
    output reg [7:0]  en_reg_pwm_7_0,
    output reg [15:8] en_reg_pwm_15_8,
    output reg [7:0]  pwm_duty_cycle
);  

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            en_reg_out_7_0  <= 8'h00
            en_reg_out_15_8 <= 8'h00
            en_reg_pwm_7_0  <= 8'h00
            en_reg_pwm_15_8 <= 8'h00
            pwm_duty_cycle  <= 8'h00
        end
        // future spi
    end

endmodule