-- Adapted from <https://github.com/yuki/pandoc-filter-tabularray/blob/f98c9050d0e1bad8cf46e01d49a5c529890861a0/filter.lua>.
-- Further extended from <https://github.com/jgm/pandoc/issues/1023#issuecomment-2480791205>
function get_rows_data(rows)
	local data = ""
	for j, row in ipairs(rows) do
		for k, cell in ipairs(row.cells) do
			data = data .. pandoc.utils.stringify(cell.contents)
			if k == #row.cells then
				data = data .. " \\\\ \n"
			else
				data = data .. " & "
			end
			-- Escape % as \%
			data = data:gsub("([^\\])%%", "%1\\%%")
			data = data:gsub("^%%", "\\%%")
		end
	end
	return data
end

function generate_tabular(tbl)
	local col_specs = tbl.colspecs
	local col_specs_latex = ""
	for i, col_spec in ipairs(col_specs) do
		local align = col_spec[1]
		if align == "AlignLeft" then
			col_specs_latex = col_specs_latex .. "l"
		elseif align == "AlignRight" then
			col_specs_latex = col_specs_latex .. "r"
		else -- align == "AlignCenter"
			col_specs_latex = col_specs_latex .. "c"
		end
	end

	local tabular_blocks = pandoc.List:new({
        pandoc.RawBlock("latex", "\\centering"),
        pandoc.RawBlock("latex", "\\begin{tabular}{" .. col_specs_latex .. "}"),
        pandoc.RawBlock("latex", "\\toprule"),
    })

	-- HEADER
	local header_latex = get_rows_data(tbl.head.rows)
	tabular_blocks = tabular_blocks
		.. pandoc.List:new({ pandoc.RawBlock("latex", header_latex), pandoc.RawBlock("latex", "\\midrule") })

	-- ROWS
	local rows_latex = ""
	for j, tablebody in ipairs(tbl.bodies) do
		rows_latex = get_rows_data(tablebody.body)
	end
	tabular_blocks = tabular_blocks .. pandoc.List:new({ pandoc.RawBlock("latex", rows_latex) })

	-- FOOTER
	local footer_latex = get_rows_data(tbl.foot.rows)
	tabular_blocks = tabular_blocks .. pandoc.List:new({ pandoc.RawBlock("latex", footer_latex) })

	tabular_blocks = tabular_blocks
		.. pandoc.List:new({
			pandoc.RawBlock("latex", "\\bottomrule"),
			pandoc.RawBlock("latex", "\\end{tabular}"),
		})

	-- CAPTION BELOW TABLE
	if tbl.caption and (tbl.caption.long or #tbl.caption > 0) then
        local caption_text
        if tbl.caption.long then
            caption_text = pandoc.utils.stringify(tbl.caption.long)
        else
            caption_text = pandoc.utils.stringify(tbl.caption)
        end
        if caption_text ~= "" then
            tabular_blocks = tabular_blocks .. pandoc.List:new({
                pandoc.RawBlock("latex", "\\caption{" .. caption_text .. "}"),
            })
        end
    end

	-- Wrap in table environment
    local result = pandoc.List:new({
        pandoc.RawBlock("latex", "\\begin{table}[ht]"),
    })
    result = result .. tabular_blocks
    result = result .. pandoc.List:new({
        pandoc.RawBlock("latex", "\\end{table}"),
    })

	return result
end

if FORMAT:match("latex") then
	function Table(tbl)
		return generate_tabular(tbl)
	end

	function RawBlock(raw)
		if raw.format:match("html") and raw.text:match("%<table") then
			blocks = pandoc.read(raw.text, raw.format).blocks
			for i, block in ipairs(blocks) do
				if block.t == "Table" then
					return generate_tabular(block)
				end
			end
		end
	end
end
