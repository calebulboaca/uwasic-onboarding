`default_nettype none

module spi_peripheral #(
    parameter max_address = 1h'4
) (
    input wire clk,
    input wire rst_n,
    input wire COPI,
    input wire nCS,
    input wire SCLK,

    output reg [7:0]  en_reg_out_7_0,
    output reg [7:0] en_reg_out_15_8,
    output reg [7:0]  en_reg_pwm_7_0,
    output reg [7:0] en_reg_pwm_15_8,
    output reg [7:0]  pwm_duty_cycle
);  

    reg COPI_sync1;
    reg COPI_sync2;
    
    reg nCS_sync1;
    reg nCS_sync2;
    reg nCS_sync3;

    reg SCLK_sync1;
    reg SCLK_sync2;
    reg SCLK_sync3;

    reg [7:0] SCLK_counter;
    reg [15:0] shift_reg;

    reg transaction_ready;
    reg transaction_processed;

    wire nCS_posedge;
    wire nCS_negedge;
    wire SCLK_posedge;

    assign nCS_posedge = nCS_sync2 && !nCS_sync3;
    assign nCS_negedge = !nCS_sync2 && nCS_sync3;
    assign SCLK_posedge = SCLK_sync2 && !SCLK_sync3;

    //Synchronizers block
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            COPI_sync1 <= 1'b0;
            COPI_sync2 <= 1'b0;
            nCS_sync1 <= 1'b1;
            nCS_sync2 <= 1'b1;
            nCS_sync3 <= 1'b1;
            SCLK_sync1 <= 1'b0;
            SCLK_sync2 <= 1'b0;
            SCLK_sync3 <= 1'b0;

        end else begin
            COPI_sync1 <= COPI;
            COPI_sync2 <= COPI_sync1;

            nCS_sync1 <= nCS;
            nCS_sync2 <= nCS_sync1;
            nCS_sync3 <= nCS_sync2;

            SCLK_sync1 <= SCLK;
            SCLK_sync2 <= SCLK_sync1;
            SCLK_sync3 <= SCLK_sync2;
        end

    end

    //Capture logic, process SPI protocol in the clk domain
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            transaction_ready <= 1'b0;
        end else if (nCS_sync2 == 1'b0) begin

            // during transaction, processing


        end else begin
            // nCS goes high, end of transaction, validate ready
            if (nCS_posedge) begin
                transaction_ready <= 1'b1;
            end else if (transaction_processed) begin
                //Reset transaction_ready after transaction processed
                transaction_ready <= 1'b0;
            end


        end

    end

    //Register updates when transaction_ready (end of nCS = 0 period)
    always @(posedge clk or negedge rst_n) begin 
        if (!rst_n) begin
            en_reg_out_7_0  <= 8'h00;
            en_reg_out_15_8 <= 8'h00;
            en_reg_pwm_7_0  <= 8'h00;
            en_reg_pwm_15_8 <= 8'h00;
            pwm_duty_cycle  <= 8'h00;
            transaction_processed <= 1'b0;
        end else if (transaction_ready && !transaction_processed) begin
            //Transaction is ready and not yet processed

            // process transaction

            transaction_processed <= 1'b1;
        end else if (!transaction_ready && transaction_processed) begin
            //Reset transaction_processed when no longer ready
            transaction_processed <= 1'b0;
        end
    end

    

endmodule