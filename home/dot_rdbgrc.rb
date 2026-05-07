# Custom rdbg command helpers loaded by debug.gem at startup.

require 'json'
module RdbgClaudePrompt
  MAX_SOURCE_LINES = 15
  MAX_LOCALS = 20
  MAX_PREVIEW_LENGTH = 700
  MAX_TRANSCRIPT_ENTRIES = 80
  MAX_TRANSCRIPT_RENDERED = 40
  MAX_TRANSCRIPT_TEXT = 4_000
  MAX_APP_FRAMES = 12
  MAX_BREAKPOINTS = 20
  APP_FRAME_PATH_MARKERS = ['/app/', '/test/', '/spec/', '/lib/'].freeze

  @session_id = nil
  @transcript = []
  @transcript_mutex = Mutex.new

  class << self
    attr_accessor :session_id

    def register!
      return unless defined?(DEBUGGER__::SESSION)

      install_transcript_capture!

      DEBUGGER__::SESSION.send(:register_command, 'claude', 'prompt', unsafe: false) do |arg|
        ask(arg)
        :retry
      end
    rescue StandardError => err
      warn "rdbg claude command setup failed: #{err.class}: #{err.message}"
    end

    def ask(arg)
      question = arg.to_s.strip
      question = 'What should I inspect next? Suggest the most useful rdbg commands.' if question.empty?

      payload = {
        question: question,
        reasoning: 'm',
        debugger_context: render_context,
        metadata: metadata,
        session_id: RdbgClaudePrompt.session_id
      }

      stdout, status = run_helper(JSON.generate(payload))

      unless status.success?
        details = stdout.strip
        details = 'no output from helper script' if details.empty?
        puts "claude prompt failed (#{status.exitstatus}): #{details}"
        return
      end

      begin
        response = JSON.parse(stdout)
        RdbgClaudePrompt.session_id = response['session_id'] if response['session_id']
        puts response['text'].to_s.strip
      rescue JSON::ParserError
        puts stdout.strip
      end
    rescue SystemCallError => err
      puts "claude prompt failed: #{err.class}: #{err.message}"
    end

    def render_context
      tc = DEBUGGER__::ThreadClient.current
      frame = tc.current_frame

      sections = []
      sections << render_frame(tc, frame)
      sections << render_source(frame)
      sections << render_locals(tc, frame)
      sections << render_backtrace(tc)
      sections << render_app_frames(tc)
      sections << render_breakpoints
      sections << render_transcript
      sections.compact.join("\n\n")
    rescue StandardError => err
      "Could not capture rdbg context: #{err.class}: #{err.message}"
    end

    def render_frame(tc, frame)
      return 'Current frame: unavailable' unless frame

      selected_frame = tc.instance_variable_get(:@current_frame_index)
      total_frames = tc.instance_variable_get(:@target_frames)&.length

      [
        'Current frame:',
        "selected_frame_index: #{selected_frame || 'unknown'}",
        "total_frames: #{total_frames || 'unknown'}",
        "name: #{frame.name}",
        "location: #{frame.location_str}",
        "self: #{preview(frame.self)}"
      ].join("\n")
    end

    def render_source(frame)
      return unless frame&.path && frame.location
      return unless File.file?(frame.path)

      line = frame.location.lineno
      start_line = [line - (MAX_SOURCE_LINES / 2), 1].max
      end_line = line + (MAX_SOURCE_LINES / 2)

      lines = File.readlines(frame.path, chomp: true)
      body = (start_line..[end_line, lines.length].min).map do |lineno|
        marker = lineno == line ? '=>' : '  '
        "#{marker} #{lineno}: #{lines[lineno - 1]}"
      end

      (["Source around current line:"] + body).join("\n")
    rescue StandardError => err
      "Source around current line: unavailable (#{err.class}: #{err.message})"
    end

    def render_locals(tc, frame)
      return 'Locals: unavailable' unless frame

      locals = tc.collect_locals(frame).first(MAX_LOCALS).map do |name, value|
        "#{name}: #{preview(value)}"
      end

      return 'Locals: none' if locals.empty?

      (["Locals:"] + locals).join("\n")
    rescue StandardError => err
      "Locals: unavailable (#{err.class}: #{err.message})"
    end

    def render_backtrace(tc)
      frames = tc.instance_variable_get(:@target_frames)
      return 'Backtrace: unavailable' unless frames

      body = frames.first(8).each_with_index.map do |frame, index|
        "#{index}: #{frame.name} at #{frame.location_str}"
      end

      (["Backtrace:"] + body).join("\n")
    rescue StandardError => err
      "Backtrace: unavailable (#{err.class}: #{err.message})"
    end

    def render_app_frames(tc)
      frames = tc.instance_variable_get(:@target_frames)
      return 'App/test frames: unavailable' unless frames

      selected_frame = tc.instance_variable_get(:@current_frame_index)
      body = frames.each_with_index.filter_map do |frame, index|
        path = frame_path(frame)
        next unless app_frame_path?(path)

        marker = index == selected_frame ? '=>' : '  '
        "#{marker} #{index}: #{frame.name} at #{frame.location_str}"
      end.first(MAX_APP_FRAMES)

      return 'App/test frames: none in current backtrace' if body.empty?

      (["App/test frames:"] + body).join("\n")
    rescue StandardError => err
      "App/test frames: unavailable (#{err.class}: #{err.message})"
    end

    def render_breakpoints
      bps = DEBUGGER__::SESSION.instance_variable_get(:@bps)
      return 'Breakpoints: unavailable' unless bps

      body = []
      bps.each_value do |bp|
        next if bp.respond_to?(:deleted?) && bp.deleted?

        body << "#{body.length}: #{strip_ansi(bp.to_s)}"
        break if body.length >= MAX_BREAKPOINTS
      end

      return 'Breakpoints: none' if body.empty?

      (["Breakpoints:"] + body).join("\n")
    rescue StandardError => err
      "Breakpoints: unavailable (#{err.class}: #{err.message})"
    end

    def install_transcript_capture!
      prepend_once(DEBUGGER__::SESSION.class, TranscriptSession)
      prepend_once(DEBUGGER__::UI_LocalConsole, TranscriptUI) if defined?(DEBUGGER__::UI_LocalConsole)
      prepend_once(DEBUGGER__::UI_ServerBase, TranscriptUI) if defined?(DEBUGGER__::UI_ServerBase)
    end

    def prepend_once(klass, mod)
      return if klass.ancestors.include?(mod)

      klass.prepend(mod)
    end

    def record_input(line)
      text = line.to_s.strip
      return if text.empty?
      return if text.start_with?('claude')

      record_transcript(:input, text)
    end

    def record_output(value)
      text =
        case value
        when Array
          value.map(&:to_s).join("\n")
        when nil
          ''
        else
          value.to_s
        end

      text = text.strip
      return if text.empty?

      record_transcript(:output, text)
    end

    def record_transcript(kind, text)
      text = text[0, MAX_TRANSCRIPT_TEXT]

      @transcript_mutex.synchronize do
        @transcript << [kind, text]
        @transcript.shift while @transcript.length > MAX_TRANSCRIPT_ENTRIES
      end
    rescue StandardError
      nil
    end

    def render_transcript
      entries = @transcript_mutex.synchronize { @transcript.last(MAX_TRANSCRIPT_RENDERED).dup }
      return 'Recent rdbg transcript: none captured yet' if entries.empty?

      body = entries.map do |kind, text|
        label = kind == :input ? 'input' : 'output'
        "#{label}: #{text}"
      end

      (["Recent rdbg transcript (oldest to newest):"] + body).join("\n")
    rescue StandardError => err
      "Recent rdbg transcript: unavailable (#{err.class}: #{err.message})"
    end

    def frame_path(frame)
      frame.respond_to?(:path) ? frame.path.to_s : frame.location_str.to_s
    end

    def app_frame_path?(path)
      APP_FRAME_PATH_MARKERS.any? { |marker| path.include?(marker) }
    end

    def strip_ansi(text)
      text.to_s.gsub(/\e\[[0-9;]*m/, '')
    end

    def metadata
      {
        ruby_version: RUBY_VERSION,
        debug_version: Gem.loaded_specs['debug']&.version&.to_s,
        rails_env: (Rails.env if defined?(Rails) && Rails.respond_to?(:env)),
        pwd: Dir.pwd
      }.compact
    end

    def preview(value)
      text = DEBUGGER__.safe_inspect(value, short: true)
      text.length > MAX_PREVIEW_LENGTH ? "#{text[0, MAX_PREVIEW_LENGTH]}..." : text
    end

    def helper_env
      env = { 'RUBY_DEBUG_ENABLE' => '0', 'RUBY_DEBUG_ADDED_RUBYOPT' => nil }
      rubyopt = ENV['RUBYOPT'].to_s
      added = ENV['RUBY_DEBUG_ADDED_RUBYOPT'].to_s

      if !rubyopt.empty? && !added.empty?
        env['RUBYOPT'] = rubyopt.split.reject { |entry| entry == added }.join(' ')
      end

      env
    end

    def run_helper(stdin_data)
      output = IO.popen(
        [helper_env, File.expand_path('~/.local/bin/rdbg-agent-prompt')],
        'r+',
        err: [:child, :out]
      ) do |io|
        io.write(stdin_data)
        io.close_write
        io.read
      end

      [output, $?]
    end
  end

  module TranscriptSession
    def process_command(line)
      RdbgClaudePrompt.record_input(line)
      super
    end
  end

  module TranscriptUI
    def puts(str = nil)
      RdbgClaudePrompt.record_output(str)
      super
    end
  end
end

RdbgClaudePrompt.register!
