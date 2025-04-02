import React from 'react';
import { Row, Col } from 'react-bootstrap';
import TokenUsageWidget from './TokenUsageWidget';

interface ConversationHeaderProps {
  title?: string;
}

/**
 * Header component for conversations dashboard that includes token usage widget
 */
const ConversationHeader: React.FC<ConversationHeaderProps> = ({ title = 'Conversations' }) => {
  return (
    <Row className="mb-4 align-items-center">
      <Col>
        <h1 className="mb-0">{title}</h1>
      </Col>
      <Col xs={12} md={3}>
        <TokenUsageWidget />
      </Col>
    </Row>
  );
};

export default ConversationHeader;